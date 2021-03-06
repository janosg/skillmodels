"""Tests for functions in simulate_data module."""
from unittest import mock

import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_array_almost_equal as aaae
from pandas.testing import assert_frame_equal as adfeq

import skillmodels.simulation.simulate_data as sd


# ===============================
# test measuerments_from_factors
# ===============================
@pytest.fixture
def set_up_meas():
    out = {}
    out["factors"] = np.array([[0, 0, 0], [1, 1, 1]])
    out["controls"] = np.array([[1, 1], [1, 1]])
    out["loadings"] = np.array([[0.3, 0.3, 0.3], [0.3, 0.3, 0.3], [0.3, 0.3, 0.3]])
    out["control_coeffs"] = np.array([[0.5, 0.5], [0.5, 0.5], [0.5, 0.5]])
    out["variances"] = np.zeros(3)
    return out


@pytest.fixture
def expected_meas():
    out = np.array([[1, 1, 1], [1.9, 1.9, 1.9]])
    return out


def test_measurements_from_factors(set_up_meas, expected_meas):
    aaae(sd.measurements_from_factors(**set_up_meas), expected_meas)


# =========================
# Test next_period_factors
# =========================


@pytest.fixture
def set_up_npfac():
    out = {}
    out["factors"] = np.array([[0.5, 0.5, 0.5, 0.5, 0.5, 0.5], [1, 1, 1, 1, 1, 1]])
    out["transition_names"] = [
        "translog",
        "linear",
        "log_ces",
        "linear",
        "constant",
        "linear",
    ]
    out["transition_argument_dicts"] = [
        {
            "coeffs": np.array([0.02] * 28),
            "included_positions": np.array([0, 1, 2, 3, 5]),
        },
        {
            "coeffs": np.array([0.2, 0.3, 0.2, 0.3, 0.2, 0.2, 0.0]),
            "included_positions": np.array([0, 1, 2, 3, 4, 5]),
        },
        {
            "coeffs": np.array([0.1, 0.1, 0.4, 0.4, 0.5, 0.5, 0.6]),
            "included_positions": [0, 1, 2, 3, 4, 5],
        },
        {"coeffs": np.array([2, 0.0]), "included_positions": np.array([1])},
        {"coeffs": np.array([1]), "included_positions": np.array([1])},
        {
            "coeffs": np.array([0.2, 0.3, 0.2, 0.3, 0.2, 0.2, 0.05]),
            "included_positions": np.array([0, 1, 2, 3, 4, 5]),
        },
    ]
    out["shock_sd"] = np.array([0, 0, 0, 0, 0, 0])
    return out


@pytest.fixture
def expected_npfac():
    # The values have been computed by using the functions from the module transition_
    # functions.py since the main calculations are made through those functions,
    # what the test actualy tests is whether the loops of getatr in #
    # simlated_next_period_factors work correctly
    d = {}
    d["tl"] = np.array([[0.145, 0.42]])
    d["lin"] = np.array([[0.7, 1.4]])
    d["lces"] = np.array([[1.6552453, 2.1552453]])
    d["ar1"] = np.array([[1, 2]])
    d["constant"] = np.array([[0.5, 1]])
    d["linwc"] = np.array([[0.75, 1.45]])
    npfac = np.concatenate(list(d.values())).T
    return npfac


def test_next_period_factors(set_up_npfac, expected_npfac):
    aaae(sd.next_period_factors(**set_up_npfac), expected_npfac)


# ===============================
# test generate datasets, nmixtures=1
# ===============================


@pytest.fixture
def set_up_generate_datasets():
    out = {}
    out["factor_names"] = ["f1", "f2"]
    out["control_names"] = ["c1", "c2"]
    out["nobs"] = 5
    out["nper"] = 3
    means = np.array([0, 0, 0.5, 0.5])
    covs = np.zeros((4, 4))
    out["dist_name"] = "_mv_student_t"
    out["dist_arg_dict"] = [{"mean": means, "cov": covs, "d_f": 3}]
    out["weights"] = 1
    out["transition_names"] = ["linear", "linear"]
    out["transition_argument_dicts"] = [
        [
            {"coeffs": np.array([0.2, 0.2, 0.0]), "included_positions": [0, 1]},
            {"coeffs": np.array([0.2, 0.2, 0.3]), "included_positions": [0, 1]},
        ]
    ] * out["nper"]
    out["shock_sd"] = [np.zeros(2)] * out["nper"]

    loadings_df = pd.DataFrame(
        data=[[0.5, 0.4], [0.2, 0.7]] * out["nper"], columns=out["factor_names"]
    )
    loadings_df["period"] = np.repeat(np.arange(out["nper"]), 2)
    loadings_df["variable"] = ["m1", "m2"] * out["nper"]
    loadings_df.set_index(["period", "variable"], inplace=True)
    out["loadings_df"] = loadings_df
    out["control_coeffs"] = [np.array([[0, 0.5, 0.3], [0, 0.5, 0.6]])] * out["nper"]
    out["meas_variances"] = pd.Series(
        data=np.zeros(len(loadings_df)), index=loadings_df.index
    )
    out["policies"] = [
        {"period": 0, "factor": "f1", "effect_size": 0.2, "standard_deviation": 0.0},
        {"period": 1, "factor": "f2", "effect_size": 0.1, "standard_deviation": 0.0},
    ]  # fac2 works only for p2
    return out


@pytest.fixture
def expected_dataset():
    out = {}
    id_obs = np.array([0, 1, 2, 3, 4] * 3)
    controls = pd.DataFrame(
        data=np.array([[0.5, 0.5]] * 15), columns=["c1", "c2"], index=id_obs
    )  # constant over time
    controls["constant"] = 1
    states_p0 = np.array([[0.2, 0]] * 5)  # setup[means][0:2]
    states_p1 = np.array(
        [[0.04, 0.44]] * 5
    )  # transition_name(states_p0), called manually
    states_p2 = np.array(
        [[0.096, 0.396]] * 5
    )  # transition_name(states_p1), called manually
    meas_p0 = np.array(
        [[0.5, 0.59]] * 5
    )  # meas_from_factor(factors_p0,controls), called manually
    meas_p1 = np.array(
        [[0.596, 0.866]] * 5
    )  # meas_from_factor(factors_p1,controls), called manually
    meas_p2 = np.array(
        [[0.6064, 0.8464]] * 5
    )  # meas_from_factor(factors_p2,controls), called manually
    periods = np.repeat(np.arange(3), 5).reshape(15, 1)
    meas = pd.DataFrame(
        data=np.concatenate(
            (periods, np.concatenate((meas_p0, meas_p1, meas_p2))), axis=1
        ),
        columns=["period", "m1", "m2"],
        index=id_obs,
    )

    latent_data = pd.DataFrame(
        data=np.concatenate(
            (periods, np.concatenate((states_p0, states_p1, states_p2))), axis=1
        ),
        columns=["period", "f1", "f2"],
        index=id_obs,
    )

    observed_data = pd.concat([controls, meas], axis=1)

    for df in [observed_data, latent_data]:
        df["period"] = df["period"].astype(int)
        df["id"] = df.index
        df.sort_values(["id", "period"], inplace=True)
        df.set_index(["id", "period"], inplace=True)
    out["observed_data"] = observed_data
    out["latent_data"] = latent_data
    return out


def test_simulate_latent_data(set_up_generate_datasets, expected_dataset):
    latent_data = sd.simulate_datasets(**set_up_generate_datasets)[1]
    adfeq(latent_data, expected_dataset["latent_data"], check_dtype=False)


def test_simulate_observed_data(set_up_generate_datasets, expected_dataset):
    obs_data = sd.simulate_datasets(**set_up_generate_datasets)[0]
    adfeq(obs_data, expected_dataset["observed_data"], check_dtype=False)


# =================
# test with nmixtures=2
# =================


@pytest.fixture
def set_up_generate_datasets_2_mix():
    out = {}
    out["factor_names"] = ["f1", "f2"]
    out["control_names"] = ["c1", "c2"]
    out["nobs"] = 5
    out["nper"] = 3
    means = np.array([[0, 0, 0.5, 0.5], [0, 0, 0.5, 0.5]])
    covs = np.zeros((2, 4, 4))
    out["dist_name"] = "multivariate_normal"
    out["dist_arg_dict"] = [
        {"mean": means[0], "cov": covs[0]},
        {"mean": means[1], "cov": covs[1]},
    ]
    out["weights"] = np.array([0.5, 0.5])
    out["transition_names"] = ["linear", "linear"]
    out["transition_argument_dicts"] = [
        [
            {"coeffs": np.array([0.2, 0.2, 0.0]), "included_positions": [0, 1]},
            {"coeffs": np.array([0.2, 0.2, 0.3]), "included_positions": [0, 1]},
        ]
    ] * (out["nper"] - 1)
    out["shock_sd"] = [np.zeros(2)] * (out["nper"] - 1)
    loadings_df = pd.DataFrame(
        data=[[0.5, 0.5], [0.6, 0.6]] * out["nper"], columns=out["factor_names"]
    )
    loadings_df["period"] = np.repeat(np.arange(out["nper"]), 2)
    loadings_df["variable"] = ["m1", "m2"] * out["nper"]
    loadings_df.set_index(["period", "variable"], inplace=True)
    out["loadings_df"] = loadings_df
    out["control_coeffs"] = [np.array([[0, 0.5, 0.5], [0, 0.6, 0.6]])] * out["nper"]
    out["meas_variances"] = pd.Series(
        data=np.zeros(len(loadings_df)), index=loadings_df.index
    )
    return out


@pytest.fixture
def expected_dataset_2_mix():
    out = {}
    id_obs = np.array([0, 1, 2, 3, 4] * 3)
    controls = pd.DataFrame(
        data=np.array([[0.5, 0.5]] * 15), columns=["c1", "c2"], index=id_obs
    )  # constant over time
    controls["constant"] = 1
    states_p0 = np.array([[0, 0]] * 5)
    states_p1 = np.array([[0, 0.3]] * 5)
    states_p2 = np.array([[0.06, 0.36]] * 5)
    meas_p0 = np.array([[0.5, 0.6]] * 5)
    meas_p1 = np.array([[0.65, 0.78]] * 5)
    meas_p2 = np.array([[0.71, 0.852]] * 5)
    periods = np.repeat(np.arange(3), 5).reshape(15, 1)
    meas = pd.DataFrame(
        data=np.concatenate(
            (periods, np.concatenate((meas_p0, meas_p1, meas_p2))), axis=1
        ),
        columns=["period", "m1", "m2"],
        index=id_obs,
    )

    latent_data = pd.DataFrame(
        data=np.concatenate(
            (periods, np.concatenate((states_p0, states_p1, states_p2))), axis=1
        ),
        columns=["period", "f1", "f2"],
        index=id_obs,
    )
    observed_data = pd.concat([controls, meas], axis=1)
    for df in [observed_data, latent_data]:
        df["period"] = df["period"].astype(int)
        df["id"] = df.index
        df.sort_values(["id", "period"], inplace=True)
        df.set_index(["id", "period"], inplace=True)
    out["observed_data"] = observed_data
    out["latent_data"] = latent_data
    return out


def test_simulate_latent_data_2_mix(
    set_up_generate_datasets_2_mix, expected_dataset_2_mix
):
    latent_data = sd.simulate_datasets(**set_up_generate_datasets_2_mix)[1]
    adfeq(latent_data, expected_dataset_2_mix["latent_data"], check_dtype=False)


def test_simulate_observed_data_2_mix(
    set_up_generate_datasets_2_mix, expected_dataset_2_mix
):
    obs_data = sd.simulate_datasets(**set_up_generate_datasets_2_mix)[0]
    adfeq(obs_data, expected_dataset_2_mix["observed_data"], check_dtype=False)


@pytest.fixture
def set_up_generate_datasets_mock():
    out = {}
    out["factor_names"] = ["f1", "f2"]
    out["control_names"] = ["c1", "c2"]
    out["nobs"] = 5
    out["nper"] = 3
    means = np.array([0, 0, 0.5, 0.5])
    covs = np.eye(4)
    out["dist_name"] = "multivariate_normal"
    out["dist_arg_dict"] = {"mean": means, "cov": covs}
    out["weights"] = 1
    out["transition_names"] = ["linear", "linear"]
    out["transition_argument_dicts"] = [
        [
            {"coeffs": np.array([0.2, 0.2, 0.0]), "included_positions": [0, 1]},
            {"coeffs": np.array([0.2, 0.2, 0.3]), "included_positions": [0, 1]},
        ]
    ] * out["nper"]
    out["shock_sd"] = [np.zeros(2)] * out["nper"]
    loadings_df = pd.DataFrame(
        data=[[0.5, 0.5], [0.5, 0.5]] * out["nper"], columns=out["factor_names"]
    )
    loadings_df["period"] = np.repeat(np.arange(out["nper"]), 2)
    loadings_df["variable"] = ["m1", "m2"] * out["nper"]
    loadings_df.set_index(["period", "variable"], inplace=True)
    out["loadings_df"] = loadings_df
    out["control_coeffs"] = [np.array([[0, 0.5, 0.5], [0, 0.5, 0.5]])] * out["nper"]
    out["meas_variances"] = pd.Series(
        data=np.zeros(len(loadings_df)), index=loadings_df.index
    )

    return out


@pytest.fixture
def expected_dataset_mock():
    out = {}
    id_obs = np.array([0, 1, 2, 3, 4] * 3)
    controls = pd.DataFrame(
        data=np.array([[0.5, 0.5]] * 15), columns=["c1", "c2"], index=id_obs
    )  # constant over time
    controls["constant"] = 1
    states_p0 = np.array([[0, 0]] * 5)  # setup[means][0:2]
    states_p1 = np.array([[0, 0.3]] * 5)  # transition_name(states_p0), called manually
    states_p2 = np.array(
        [[0.06, 0.36]] * 5
    )  # transition_name(states_p1), called manually
    meas_p0 = np.array(
        [[0.5, 0.5]] * 5
    )  # meas_from_factor(factors_p0,controls), called manually
    meas_p1 = np.array(
        [[0.65, 0.65]] * 5
    )  # meas_from_factor(factors_p1,controls), called manually
    meas_p2 = np.array(
        [[0.71, 0.71]] * 5
    )  # meas_from_factor(factors_p2,controls), called manually
    periods = np.array([[0] * 5, [1] * 5, [2] * 5]).reshape(15, 1)
    meas = pd.DataFrame(
        data=np.concatenate(
            (periods, np.concatenate((meas_p0, meas_p1, meas_p2))), axis=1
        ),
        columns=["period", "m1", "m2"],
        index=id_obs,
    )

    latent_data = pd.DataFrame(
        data=np.concatenate(
            (periods, np.concatenate((states_p0, states_p1, states_p2))), axis=1
        ),
        columns=["period", "f1", "f2"],
        index=id_obs,
    )
    observed_data = pd.concat([controls, meas], axis=1)

    for df in [observed_data, latent_data]:
        df["period"] = df["period"].astype(int)
        df["id"] = df.index
        df.sort_values(["id", "period"], inplace=True)
        df.set_index(["id", "period"], inplace=True)
    out["observed_data"] = observed_data
    out["latent_data"] = latent_data

    return out


# patch the gen_data_function
@mock.patch(
    "skillmodels.simulation.simulate_data."
    + "generate_start_factors_and_control_variables_elliptical",
    return_value=(np.array([[0, 0]] * 5), np.array([[1, 0.5, 0.5]] * 5)),
    autospec=True,
)
def test_simulate_latent_data_with_mock(
    mock_generate_start_factors_and_control_variables,
    set_up_generate_datasets_mock,
    expected_dataset_mock,
):
    results = sd.simulate_datasets(**set_up_generate_datasets_mock)
    adfeq(results[1], expected_dataset_mock["latent_data"], check_dtype=False)


@mock.patch(
    "skillmodels.simulation.simulate_data."
    + "generate_start_factors_and_control_variables_elliptical",
    return_value=(np.array([[0, 0]] * 5), np.array([[1, 0.5, 0.5]] * 5)),
    autospec=True,
)
def test_simulate_observed_data_with_mock(
    mock_generate_start_factors_and_control_variables,
    set_up_generate_datasets_mock,
    expected_dataset_mock,
):
    results = sd.simulate_datasets(**set_up_generate_datasets_mock)
    adfeq(results[0], expected_dataset_mock["observed_data"], check_dtype=False)


# =========================
# generate datasets nmixtures=2
# =========================


@pytest.fixture
def set_up_generate_datasets_mock_mix_2():
    out = {}
    out["factor_names"] = ["f1", "f2"]
    out["control_names"] = ["c1", "c2"]
    out["nobs"] = 5
    out["nper"] = 3
    means = np.array([[0, 0, 0.5, 0.5], [0, 0, 0.5, 0.8]])
    covs = np.array([np.eye(4) * 100] * 2)
    out["dist_name"] = "_mv_student_t"
    out["dist_arg_dict"] = [
        {"mean": means[0], "cov": covs[0]},
        {"mean": means[1], "cov": covs[1]},
    ]
    out["weights"] = np.array([0.5, 0.5])
    out["transition_names"] = ["linear", "linear"]
    out["transition_argument_dicts"] = [
        [
            {"coeffs": np.array([0.2, 0.2, 0.0]), "included_positions": [0, 1]},
            {"coeffs": np.array([0.2, 0.2, 0.3]), "included_positions": [0, 1]},
        ]
    ] * (out["nper"] - 1)
    out["shock_sd"] = [np.zeros(2)] * (out["nper"] - 1)
    loadings_df = pd.DataFrame(
        data=[[0.5, 0.5], [0.5, 0.5]] * out["nper"], columns=out["factor_names"]
    )
    loadings_df["period"] = np.repeat(np.arange(out["nper"]), 2)
    loadings_df["variable"] = ["m1", "m2"] * out["nper"]
    loadings_df.set_index(["period", "variable"], inplace=True)
    out["loadings_df"] = loadings_df
    out["control_coeffs"] = [np.array([[0, 0.5, 0.5], [0, 0.5, 0.5]])] * out["nper"]
    out["meas_variances"] = pd.Series(
        data=np.zeros(len(loadings_df)), index=loadings_df.index
    )
    return out


@pytest.fixture
def expected_dataset_mock_mix_2():
    out = {}
    id_obs = np.array([0, 1, 2, 3, 4] * 3)
    controls = pd.DataFrame(
        data=np.array([[0.5, 0.5]] * 15), columns=["c1", "c2"], index=id_obs
    )  # constant over time
    controls["constant"] = 1

    states_p0 = np.array([[0, 0]] * 5)  # setup[means][0:2]
    states_p1 = np.array([[0, 0.3]] * 5)  # transition_name(states_p0), called manually
    states_p2 = np.array(
        [[0.06, 0.36]] * 5
    )  # transition_name(states_p1), called manually
    meas_p0 = np.array(
        [[0.5, 0.5]] * 5
    )  # meas_from_factor(factors_p0,controls), called manually
    meas_p1 = np.array(
        [[0.65, 0.65]] * 5
    )  # meas_from_factor(factors_p1,controls), called manually
    meas_p2 = np.array(
        [[0.71, 0.71]] * 5
    )  # meas_from_factor(factors_p2,controls), called manually
    periods = np.repeat(np.arange(3), 5).reshape(15, 1)
    meas = pd.DataFrame(
        data=np.concatenate(
            (periods, np.concatenate((meas_p0, meas_p1, meas_p2))), axis=1
        ),
        columns=["period", "m1", "m2"],
        index=id_obs,
    )

    latent_data = pd.DataFrame(
        data=np.concatenate(
            (periods, np.concatenate((states_p0, states_p1, states_p2))), axis=1
        ),
        columns=["period", "f1", "f2"],
        index=id_obs,
    )
    observed_data = pd.concat([controls, meas], axis=1)
    for df in [observed_data, latent_data]:
        df["period"] = df["period"].astype(int)
        df["id"] = df.index
        df.sort_values(["id", "period"], inplace=True)
        df.set_index(["id", "period"], inplace=True)
    out["observed_data"] = observed_data
    out["latent_data"] = latent_data
    return out


# # patch the gen_data_function
@mock.patch(
    "skillmodels.simulation.simulate_data."
    + "generate_start_factors_and_control_variables_elliptical",
    return_value=(np.array([[0, 0]] * 5), np.array([[1, 0.5, 0.5]] * 5)),
    autospec=True,
)
def test_simulate_latent_data_with_mock_mix_2(
    mock_generate_start_factors_and_control_variables,
    set_up_generate_datasets_mock_mix_2,
    expected_dataset_mock_mix_2,
):
    results = sd.simulate_datasets(**set_up_generate_datasets_mock_mix_2)
    adfeq(results[1], expected_dataset_mock_mix_2["latent_data"], check_dtype=False)


# # patch the gen_data_function
@mock.patch(
    "skillmodels.simulation.simulate_data."
    + "generate_start_factors_and_control_variables_elliptical",
    return_value=(np.array([[0, 0]] * 5), np.array([[1, 0.5, 0.5]] * 5)),
    autospec=True,
)
def test_simulate_observed_data_with_mock_mix_2(
    mock_generate_start_factors_and_control_variables,
    set_up_generate_datasets_mock_mix_2,
    expected_dataset_mock_mix_2,
):
    results = sd.simulate_datasets(**set_up_generate_datasets_mock_mix_2)
    adfeq(results[0], expected_dataset_mock_mix_2["observed_data"], check_dtype=False)
