from skillmodels.estimation.parse_params import parse_params
from skillmodels.fast_routines.kalman_filters import sqrt_linear_anchoring_update
from skillmodels.fast_routines.kalman_filters import sqrt_linear_update
from skillmodels.fast_routines.kalman_filters import sqrt_unscented_predict
from skillmodels.fast_routines.sigma_points import calculate_sigma_points


def log_likelihood_contributions(
    params,
    like_contributions,
    parse_params_args,
    periods,
    update_info,
    anchoring,
    update_args,
    predict_args,
    calculate_sigma_points_args,
):
    """Return the log likelihood contributions per update and individual in the sample.

    Users do not have to call this function directly and do not have to bother
    about its arguments but the function nicely shows how the likelihood
    interpretation of the Kalman filter allow to break the large likelihood
    problem of the model into many smaller problems.

    First the params vector is parsed into the many quantities that depend on
    it. See :ref:`params_and_quants` for details.

    Then, for each period of the model first all Kalman updates for the
    measurement equations are done. Each Kalman update updates the following
    quantities:

        * the state array X
        * the covariance matrices P
        * the likelihood vector like_vec
        * the weights for the mixture distribution of the factors W

    Then the predict step of the Unscented Kalman filter is applied. The
    predict step propagates the following quantities to the next period:

        * the state array X
        * the covariance matrices P

    In the last period an additional update is done to incorporate the
    anchoring equation into the likelihood.

    """
    like_contributions[:] = 0.0

    parse_params(params, **parse_params_args)

    k = 0
    for t in periods:
        nmeas = len(update_info.loc[t])
        for _j in range(nmeas):
            purpose = update_info.iloc[k]["purpose"]
            update(purpose, update_args[k])
            k += 1
        if t < periods[-1]:
            calculate_sigma_points(**calculate_sigma_points_args)
            predict(t, predict_args)

    return like_contributions


def update(purpose, update_args):
    """Select and call the correct update function.

    The actual update functions are implemented in several modules in
    :ref:`fast_routines`

    """
    if purpose == "measurement":
        sqrt_linear_update(*update_args)
    elif purpose == "anchoring":
        sqrt_linear_anchoring_update(*update_args)
    else:
        raise ValueError("purpose must be measurement or anchoring.")


def predict(period, predict_args):
    """Select and call the correct predict function.

    The actual predict functions are implemented in several modules in
    :ref:`fast_routines`

    """
    sqrt_unscented_predict(period, **predict_args)
