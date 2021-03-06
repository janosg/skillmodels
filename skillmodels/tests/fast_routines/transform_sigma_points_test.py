from unittest.mock import patch

import numpy as np
from numpy.testing import assert_array_almost_equal as aaae

from skillmodels.fast_routines.transform_sigma_points import transform_sigma_points


def fake1(arr, coeffs, included_positions):
    return (arr[:, included_positions] + coeffs).sum(axis=1)


def fake2(arr, coeffs, included_positions):
    return (arr[:, included_positions] - coeffs).sum(axis=1)


class TestTransformSigmaPoints:
    def setup(self):
        self.period = 1
        self.flat_sigma_points = np.arange(20, dtype=float).reshape(2, 10).T
        self.transition_argument_dicts = [
            [],
            [
                {"coeffs": 1, "included_positions": [0]},
                {"coeffs": 0.1, "included_positions": [0, 1]},
            ],
            [],
        ]

        self.transition_function_names = ["fake1", "fake2"]

    @patch("skillmodels.fast_routines.transform_sigma_points.trans")
    def test_tsp_no_anchoring(self, mock_trans):
        mock_trans.fake1.side_effect = fake1
        mock_trans.fake2.side_effect = fake2

        exp = np.zeros((10, 2))
        exp[:, 0] = np.arange(10) + 1
        exp[:, 1] = np.arange(start=10, stop=20) + np.arange(10) - 0.2

        transform_sigma_points(
            period=self.period,
            flat_sigma_points=self.flat_sigma_points,
            transition_argument_dicts=self.transition_argument_dicts,
            transition_function_names=self.transition_function_names,
        )

        calc = self.flat_sigma_points.copy()
        aaae(calc, exp)

    @patch("skillmodels.fast_routines.transform_sigma_points.trans")
    def test_tsp_with_anchoring_integration(self, mock_trans):
        mock_trans.fake1.side_effect = fake1
        mock_trans.fake2.side_effect = fake2

        exp = np.zeros((10, 2))
        exp[:, 0] = np.arange(10) + 1
        exp[:, 1] = np.arange(start=10, stop=20) + 0.5 * np.arange(10) - 0.1

        transform_sigma_points(
            period=self.period,
            flat_sigma_points=self.flat_sigma_points,
            transition_argument_dicts=self.transition_argument_dicts,
            transition_function_names=self.transition_function_names,
            anchoring_loadings=np.array([[[0, 0]], [[0, 2.0]], [[0, 2.0]]]),
            anchoring_positions=np.array([1]),
            anchoring_variables=[None, None, None],
        )

        calc = self.flat_sigma_points.copy()
        aaae(calc, exp)
