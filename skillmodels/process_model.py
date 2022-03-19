import inspect

import numpy as np
import pandas as pd
from dags import concatenate_functions
from dags.signature import rename_arguments
from jax import vmap
from pandas import DataFrame

import skillmodels.transition_functions as tf
from skillmodels.check_model import check_model
from skillmodels.decorators import extract_params
from skillmodels.decorators import jax_array_output


def process_model(model_dict):
    """Check, clean, extend and transform the model specs.

    Check the completeness, consistency and validity of the model specifications.

    Set default values and extend the model specification where necessary.

    Args:
        model_dict (dict): The model specification. See: :ref:`model_specs`

    Returns:
        dict: nested dictionary of model specs. It has the following entries:
        - dimensions (dict): Dimensional information like n_states, n_periods,
        n_controls, n_mixtures. See :ref:`dimensions`.
        - labels (dict): Dict of lists with labels for the model quantities like
        factors, periods, controls, stagemap and stages. See :ref:`labels`
        - anchoring (dict): Information about anchoring. See :ref:`anchoring`
        - transition_info (dict): Everything related to transition functions.
        - update_info (pandas.DataFrame): DataFrame with one row per Kalman update
        needed in the likelihood function. See :ref:`update_info`.
        - normalizations (dict): Nested dictionary with information on normalized factor
        loadings and intercepts for each factor. See :ref:`normalizations`.

    """
    dims = get_dimensions(model_dict)
    labels = _get_labels(model_dict, dims)
    anchoring = _process_anchoring(model_dict)
    check_model(model_dict, labels, dims, anchoring)
    transition_info = _get_transition_info(model_dict, labels)
    labels["transition_names"] = list(transition_info["raw_function_names"].values())

    processed = {
        "dimensions": dims,
        "labels": labels,
        "anchoring": anchoring,
        "estimation_options": _process_estimation_options(model_dict),
        "transition_info": transition_info,
        "update_info": _get_update_info(model_dict, dims, labels, anchoring),
        "normalizations": _process_normalizations(model_dict, dims, labels),
    }
    return processed


def get_dimensions(model_dict):
    """Extract the dimensions of the model.

    Args:
        model_dict (dict): The model specification. See: :ref:`model_specs`

    Returns:
        dict: Dimensional information like n_states, n_periods, n_controls,
            n_mixtures. See :ref:`dimensions`.

    """
    all_n_periods = [len(d["measurements"]) for d in model_dict["factors"].values()]

    dims = {
        "n_latent_factors": len(model_dict["factors"]),
        "n_observed_factors": len(model_dict.get("observed_factors", [])),
        "n_periods": max(all_n_periods),
        # plus 1 for the constant
        "n_controls": len(model_dict.get("controls", [])) + 1,
        "n_mixtures": model_dict["estimation_options"].get("n_mixtures", 1),
    }
    dims["n_all_factors"] = dims["n_latent_factors"] + dims["n_observed_factors"]
    return dims


def _get_labels(model_dict, dimensions):
    """Extract labels of the model quantities.

    Args:
        model_dict (dict): The model specification. See: :ref:`model_specs`
        dimensions (dict): Dimensional information like n_states, n_periods, n_controls,
            n_mixtures. See :ref:`dimensions`.

    Returns:
        dict: Dict of lists with labels for the model quantities like
        factors, periods, controls, stagemap and stages. See :ref:`labels`

    """
    stagemap = model_dict.get("stagemap", list(range(dimensions["n_periods"] - 1)))

    labels = {
        "latent_factors": sorted(model_dict["factors"]),
        "observed_factors": sorted(model_dict.get("observed_factors", [])),
        "controls": ["constant"] + sorted(model_dict.get("controls", [])),
        "periods": list(range(dimensions["n_periods"])),
        "stagemap": stagemap,
        "stages": sorted(np.unique(stagemap)),
    }

    labels["all_factors"] = labels["latent_factors"] + labels["observed_factors"]

    return labels


def _process_estimation_options(model_dict):
    """Process options.

    Args:
        model_dict (dict): The model specification. See: :ref:`model_specs`

    Returns:
        dict: Tuning parameters for the estimation. See :ref:`options`.

    """
    default_options = {
        "sigma_points_scale": 2,
        "robust_bounds": True,
        "bounds_distance": 1e-3,
        "clipping_lower_bound": -1e250,
        "clipping_upper_bound": None,
        "clipping_lower_hardness": 1,
        "clipping_upper_hardness": 1,
    }
    default_options.update(model_dict.get("estimation_options", {}))

    if not default_options["robust_bounds"]:
        default_options["bounds_distance"] = 0

    return default_options


def _process_anchoring(model_dict):
    """Process the specification that governs how latent factors are anchored.

    Args:
        model_dict (dict): The model specification. See: :ref:`model_specs`

    Returns:
        dict: Dictionary with information about anchoring. See :ref:`anchoring`

    """
    anchinfo = {
        "anchoring": False,
        "outcomes": {},
        "factors": [],
        "free_controls": False,
        "free_constant": False,
        "free_loadings": False,
        "ignore_constant_when_anchoring": False,
    }

    if "anchoring" in model_dict:
        anchinfo.update(model_dict["anchoring"])
        anchinfo["anchoring"] = True
        anchinfo["factors"] = sorted(anchinfo["outcomes"].keys())

    return anchinfo


def _get_transition_info(model_dict, labels):
    """Collect the transition functions in a nested tuple.

    Args:
        transition_names (list): Names of transition functions for each factor.

    Returns:
        tuple: Tuple of tuples of length n_periods. Each inner tuple
            has the following two entries: (name_of_transition_function, callable).

    """

    raw_functions, function_names, param_names = [], [], []
    latent_factors = labels["latent_factors"]
    all_factors = labels["all_factors"]

    for factor in labels["latent_factors"]:
        spec = model_dict["factors"][factor]["transition_function"]
        if isinstance(spec, str):
            func = getattr(tf, spec)
            if spec == "constant":
                func = rename_arguments(func, mapper={"state": factor})
            raw_functions.append(func)
            function_names.append(spec)
            param_names.append(getattr(tf, f"params_{spec}")(all_factors))
        elif callable(spec):
            raw_functions.append(spec)
            if hasattr(spec, "__name__"):
                function_names.append(spec.__name__)
            else:
                raise AttributeError(
                    "Custom transition functions must have a __name__ attribute."
                )
            if hasattr(spec, "__registered_params__"):
                param_names.append(spec.__registered_params__)
            else:
                raise AttributeError(
                    "Custom transition_functions must have a __registered_params__ "
                    "attribute. You can set it via the register_params decorator."
                )

    functions = {}
    for factor, func in zip(latent_factors, raw_functions):
        func = extract_params(func, key=factor)
        functions[f"next_{factor}"] = func

    transition_function = concatenate_functions(
        functions=functions, targets=list(functions)
    )

    transition_function = jax_array_output(transition_function)
    ordered_args = list(inspect.signature(transition_function).parameters)

    extracted_columns = {
        factor: i for i, factor in enumerate(all_factors) if factor in ordered_args
    }

    in_axes = [0] * len(ordered_args)
    in_axes[ordered_args.index("params")] = None
    in_axes = tuple(in_axes)
    transition_function = vmap(transition_function, in_axes=in_axes)

    out = {
        "func": transition_function,
        "columns": extracted_columns,
        "order": ordered_args,
        "param_names": dict(zip(latent_factors, param_names)),
        "raw_functions": dict(zip(latent_factors, raw_functions)),
        "decorated_functions": dict(zip(latent_factors, list(functions.values()))),
        "raw_function_names": dict(zip(latent_factors, function_names)),
    }
    return out


def _get_update_info(model_dict, dimensions, labels, anchoring_info):
    """Construct a DataFrame with information on each Kalman update.

    Args:
        model_dict (dict): The model specification. See: :ref:`model_specs`
        dimensions (dict): Dimensional information like n_states, n_periods, n_controls,
            n_mixtures. See :ref:`dimensions`.
        labels (dict): Dict of lists with labels for the model quantities like
            factors, periods, controls, stagemap and stages. See :ref:`labels`
        anchoring_info (dict): Information about anchoring. See :ref:`anchoring`

    Returns:
        pandas.DataFrame: DataFrame with one row per Kalman update needed in
            the likelihood function. See :ref:`update_info`.

    """
    index = pd.MultiIndex(levels=[[], []], codes=[[], []], names=["period", "variable"])
    uinfo = DataFrame(index=index, columns=labels["latent_factors"] + ["purpose"])

    measurements = {}
    for factor in labels["latent_factors"]:
        measurements[factor] = fill_list(
            model_dict["factors"][factor]["measurements"], [], dimensions["n_periods"]
        )

    for period in labels["periods"]:
        for factor in labels["latent_factors"]:
            for meas in measurements[factor][period]:
                uinfo.loc[(period, meas), factor] = True
                uinfo.loc[(period, meas), "purpose"] = "measurement"
        for factor in anchoring_info["factors"]:
            outcome = anchoring_info["outcomes"][factor]
            name = f"{outcome}_{factor}"
            uinfo.loc[(period, name), factor] = True
            uinfo.loc[(period, name), "purpose"] = "anchoring"

    uinfo.fillna(False, inplace=True)
    return uinfo


def _process_normalizations(model_dict, dimensions, labels):
    """Process the normalizations of intercepts and factor loadings.

    Args:
        model_dict (dict): The model specification. See: :ref:`model_specs`
        dimensions (dict): Dimensional information like n_states, n_periods, n_controls,
            n_mixtures. See :ref:`dimensions`.
        labels (dict): Dict of lists with labels for the model quantities like
            factors, periods, controls, stagemap and stages. See :ref:`labels`

    Returns:
        normalizations (dict): Nested dictionary with information on normalized factor
            loadings and intercepts for each factor. See :ref:`normalizations`.

    """
    normalizations = {}
    for factor in labels["latent_factors"]:
        normalizations[factor] = {}
        norminfo = model_dict["factors"][factor].get("normalizations", {})
        for norm_type in ["loadings", "intercepts"]:
            candidate = norminfo.get(norm_type, [])
            candidate = fill_list(candidate, {}, dimensions["n_periods"])
            normalizations[factor][norm_type] = candidate

    return normalizations


def fill_list(short_list, fill_value, length):
    """Extend a list to specified length by filling it with the fill_value.

    Examples:
    >>> fill_list(["a"], "b", 3)
    ['a', 'b', 'b']

    """
    res = list(short_list)
    diff = length - len(short_list)
    assert diff >= 0, "short_list has to be shorter than length."
    if diff >= 1:
        res += [fill_value] * diff
    return res


def get_period_measurements(update_info, period):
    if period in update_info.index:
        measurements = list(update_info.loc[period].index)
    else:
        measurements = []
    return measurements
