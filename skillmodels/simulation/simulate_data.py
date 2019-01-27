"""Functions to simulate a dataset generated by a latent factor model.

Notes:
    - I use abbreviations to describe the sizes of arrays. An overview is here:
        https://skillmodels.readthedocs.io/en/latest/names_and_concepts.html
    - what is called factors here is the same as states in the assignments.
    - You can use additional functions if you want. Their name should start
        with an underscore to make clear that those functions should not be
        used in any other module.
    - Please write tests for all functions except simulate_dataset.
        I know that functions involving randomness are hard to test. The
        best way is to replace (patch) the methods that actually generate
        random numbers with a so called mock function while testing. It can
        be done with this library:
        https://docs.python.org/3/library/unittest.mock.html
        I do similar stuff in many places of skillmodels but it is quite difficult,
        so you can also ask me once you get there and we can do it together.
    - The tests should be in a module in
        `skillmodels/tests/simulation/simulate_dataset_test.py.
    - Use pytest for the tests (as you learned in the lecture) even though
        the other tests in skillmodels use an older library
    - I added some import statements but you will probably need more
    - Please delete all notes in the docstrings when you are done.
    - It is very likely that I made some mistakes in the docstrings or forgot an
        argument somewhere. Just send me an email in that case or come to my office.

"""

from scipy import linalg as splin
import pandas as pd
import numpy as np
from numpy.random import multivariate_normal, uniform, multinomial
import sys
sys.path.append('../model_functions')
import transition_functions as tf

#import skillmodels.model_functions.transition_functions as tf

def simulate_datasets():
    """Simulate datasets generated by a latent factor model.

    This function calls the remaining functions in this module.

    Implement this function at the very end and only after I accepted your pull
    request for the remaining functions. You can then either figure out a suitable
    list of arguments yourself or ask me again.

    Returns:
        observed_data (pd.DataFrame): Dataset with measurements and control variables
            in long format
        latent_data (pd.DataFrame): Dataset with lantent factors in long format
    """
    pass


def generate_start_factors_and_control_variables(
        means, covs, weights, nobs, factor_names, control_names):
    """Draw initial states and control variables from a (mixture of) normals.

    Args:
        means (np.ndarray): size (nemf, nfac + ncontrols)
        covs (np.ndarray): size (nemf, nfac + ncontrols, nfac + ncontrols)
        weights (np.ndarray): size (nemf). The weight of each mixture element.
        nobs (int): number of observations

    Returns:
        start_factors (pd.DataFrame): shape (nobs, nfac),
            columns are factor_names
        controls (pd.DataFrame): shape (nobs, ncontrols),
            columns are control names

    Notes:
        In the long run I would like to generalize this to drawing from a mixture of
        elliptical distributions: https://en.wikipedia.org/wiki/Elliptical_distribution
        This contains the multivariate normal as a special case.
        It would require an interface change because the elliptical distribution has more
        parameters than just mean and covariance. It would be great if you make a proposal
        for this general case.

    """
    assert np.sum(weights) == 1 and all(i >= 0 for i in weights)
    nfac = len(factor_names)
    ncont = len(control_names)
    assert np.shape(covs)[1] == np.shape(covs)[
        2] == nfac + ncont, 'each cov matrix should be of shape (nfac+ncont,nfac+ncont)'
    out = np.zeros((nobs, nfac + ncont))
    # 1d array of length len(mixture components)
    weights_cum = np.cumsum(weights)
    u = uniform(0, 1, (nobs, 1))
    for i in range(nobs):
        # Draw vector of [states,controls] from distr j if cum_weights[j-1]<u[i]<=cum_weights[j]:
        #    Pr(cum_weights[j-1]<u[i]<=cum_weights[j])=cum_weights[j]-cum_weights[j-1]
        #    =weight[j]=Pr(the draw is from subpopulation j)
        out[i] = multivariate_normal(
            means[np.argmax(weights_cum >= u[i])], covs[np.argmax(weights_cum >= u[i])])
    start_factors = pd.DataFrame(data=out[:, 0:nfac], columns=factor_names)
    controls = pd.DataFrame(data=out[:, nfac:], columns=control_names)

    return start_factors, controls


# version 2:

def generate_start_factors_and_control_variables_v2(
        means, covs, weights, nobs, factor_names, control_names):
    """Draw initial states and control variables from a (mixture of) normals.

    Args:
        means (np.ndarray): size (nemf, nfac + ncontrols)
        covs (np.ndarray): size (nemf, nfac + ncontrols, nfac + ncontrols)
        weights (np.ndarray): size (nemf). The weight of each mixture element.
        nobs (int): number of observations

    Returns:
        start_factors (pd.DataFrame): shape (nobs, nfac),
            columns are factor_names
        controls (pd.DataFrame): shape (nobs, ncontrols),
            columns are control names

    Notes:
        In the long run I would like to generalize this to drawing from a mixture of
        elliptical distributions: https://en.wikipedia.org/wiki/Elliptical_distribution
        This contains the multivariate normal as a special case.
        It would require an interface change because the elliptical distribution has more
        parameters than just mean and covariance. It would be great if you make a proposal
        for this general case.

    """
    assert np.sum(weights) == 1 and all(i >= 0 for i in weights)
    nfac = len(factor_names)
    ncont = len(control_names)
    assert np.shape(covs)[1] == np.shape(covs)[
        2] == nfac + ncont, 'each cov matrix should be of shape (nfac+ncont,nfac+ncont)'
    out = np.zeros((nobs, nfac + ncont))
    weights = weights.reshape(weights.size)  # weights should be a 1d array
    helper_array = np.nonzero(multinomial(1, weights, size=nobs))[1]
    for i in range(nobs):
        out[i] = multivariate_normal(
            means[helper_array[i]], covs[helper_array[i]])
    start_factors = pd.DataFrame(data=out[:, 0:nfac], columns=factor_names)
    controls = pd.DataFrame(data=out[:, nfac:], columns=control_names)

    return start_factors, controls


# version 3. Avoids loops:

def generate_start_factors_and_control_variables_v3(
        means, covs, weights, nobs, factor_names, control_names):
    """Draw initial states and control variables from a (mixture of) normals.

    Args:
        means (np.ndarray): size (nemf, nfac + ncontrols)
        covs (np.ndarray): size (nemf, nfac + ncontrols, nfac + ncontrols)
        weights (np.ndarray): size (nemf). The weight of each mixture element.
        nobs (int): number of observations

    Returns:
        start_factors (pd.DataFrame): shape (nobs, nfac),
            columns are factor_names
        controls (pd.DataFrame): shape (nobs, ncontrols),
            columns are control names

    Notes:
        In the long run I would like to generalize this to drawing from a mixture of
        elliptical distributions: https://en.wikipedia.org/wiki/Elliptical_distribution
        This contains the multivariate normal as a special case.
        It would require an interface change because the elliptical distribution has more
        parameters than just mean and covariance. It would be great if you make a proposal
        for this general case.

    """
    assert np.sum(weights) == 1 and all(i >= 0 for i in weights)
    nfac = len(factor_names)
    ncont = len(control_names)
    assert np.shape(covs)[1] == np.shape(covs)[
        2] == nfac + ncont, 'each cov matrix should be of shape (nfac+ncont,nfac+ncont)'
   # out = np.zeros((nobs,nfac+ncont))
    weights = weights.reshape(weights.size)  # weights should be a 1d array
    helper_array = np.nonzero(multinomial(1, weights, size=nobs))[1]
    # Draw the entire sample from  multivariate nomal of size nobs*(nfac+ncont) with covariance matrix given by covariance matrices of each mixture on the diagonal
    agg_means = means[helper_array].reshape(nobs * (weights.size))
    agg_cov = splin.block_diag(*covs[helper_array])
    out = multivariate_normal(agg_means, agg_cov).reshape(nobs, nfac + ncont)
    start_factors = pd.DataFrame(data=out[:, 0:nfac], columns=factor_names)
    controls = pd.DataFrame(data=out[:, nfac:], columns=control_names)

    return start_factors, controls




def next_period_factors(
        factors, transition_names, transition_argument_dicts, shock_variances):
    """Apply transition function to factors and add shocks.

    Args:
        factors (pd.DataFrame): shape (nobs, nfac)
        transition_names (list): list of strings with the names of the transition
            function of each factor.
        transition_argument_dicts (list): list of dictionaries of length nfac with
            the arguments for the transition function of each factor. A detailed description
            of the arguments of transition functions can be found in the module docstring
            of skillmodels.model_functions.transition_functions.
        shock_variances (np.ndarray): numpy array of length nfac.

    Returns:
        next_factors (pd.DataFrame):

    Notes:
        - You can look at the module `transform_sigma_points` to see how you can use
        getattr() to call the transition functions based on their name

        - Writing this function is quite complex because it reuses a lot of code for
             the transition functions. Take the time to read the documentation of those
             functions if you feel it is necessary

        - The shocks for the different factors are assumed to be independent. You can draw
            them from a multivariate normal with diagonal covariance matrix or from
            nfac univariate normals.

        - You have to convert the factors to a numpy array (DataFrame.values) and then convert
            the result back in the end. For speed reasons all the transition functions
            expect numpy arrays and not pandas DataFrames.


    """
    nobs = factors.shape[0]
    nfac = factors.shape[1]
    sigma_points = factors.values
    factors_tp1 = np.zeros((nobs,nfac))
    for i in range(nfac):
       factors_tp1[:,i]=getattr(tf,transition_names[i])(sigma_points,\
                  **transition_argument_dicts[i])
    errors = multivariate_normal(np.array([0]*nfac),np.diag(shock_variances))
    factors_tp1 = factors_tp1 + errors.reshape(1,nfac)
    next_factors=pd.DataFrame(data = factors_tp1, columns = factors.columns)
    
    return next_factors


def measurements_from_factors(factors, controls, loadings, deltas, variances, measurement_names):
    """Generate the variables that would be observed in practice.

    This generates the data for only one period. Let nmeas be the number of measurements in that period.

    Args:
        factors (pd.DataFrame): DataFrame of shape (nobs, nfac)
        controls (pd.DataFrame): DataFrame of shape (nobs, ncontrols)
        loadings (np.ndarray): numpy array of size (nmeas, nfac)
        deltas (np.ndarray): numpy array of size (nmeas, ncontrols)
        variances (np.ndarray): numpy array of size (nmeas) with the variances of the
            measurements. Measurement error is assumed to be independent across measurements
        measurement_names (list): list of length nmeas with the names of the measurements

    Returns:
        measurements (pd.DataFrame): DataFrame of shape (nobs, nmeas) with measurement
            names as columns.

    Notes:
        - A measurement y is a linear function of latent factors and control variables, i.e.
            y = factors times loadings + controls times deltas + epsilon
            This is a slide extension of the measurement model you know from the assignments.
        - Try to express as much as possible in matrix products. This will lead to concise and
            fast code.
    """
    nobs = factors.shape[0]
    nfac = factors.shape[1]
    ncontrols = controls.shape[1]
    nmeas = len(measurement_names)
    epsilon = multivariate_normal([0]*nmeas,np.diag(variances),nobs).reshape(nobs,1,nmeas) 
    states = factors.values.reshape(nobs,1,nfac)
    conts = controls.values.reshape(nobs,1,ncontrols)
    meas = np.dot(states,loadings) + np.dot(conts,deltas) + epsilon
    measurements = pd.DataFrame(data = meas,columns = measurement_names)
    
    return measurements