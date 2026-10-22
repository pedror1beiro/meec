import numpy as np
import pytest
from tomsa.kinematics import differentiate, compute_kinematics


def stamps(seconds):
    return 1_760_000_000_000_000_000 + np.rint(np.array(seconds) * 1e9).astype(np.int64)


def test_irregular_quadratic_derivative_and_nanoseconds_precision():
    t = np.array([0., .000001, .000003, .000007])
    np.testing.assert_allclose(differentiate(stamps(t), t**2), 2*t, atol=1e-15)


def test_signed_speed_rate_is_not_vector_acceleration_magnitude():
    t = np.array([0., .4, 1., 1.8])
    v = np.column_stack([3 - t, np.zeros((len(t), 2))])
    k = compute_kinematics(stamps(t), v, v)
    np.testing.assert_allclose(k.speed_rate_m_s2, -1., atol=1e-12)
    np.testing.assert_allclose(k.acceleration_magnitude_m_s2, 1., atol=1e-12)
    unknown = compute_kinematics(stamps(t), v)
    assert np.isnan(unknown.acceleration_magnitude_m_s2).all()
    np.testing.assert_allclose(unknown.speed_m_s, 3-t)


def test_turning_at_constant_speed_has_vector_acceleration():
    t = np.arange(0., 1., .01)
    v = np.column_stack([np.cos(t), np.sin(t), np.zeros(len(t))])
    k = compute_kinematics(stamps(t), v, v)
    np.testing.assert_allclose(k.speed_m_s, 1., atol=1e-12)
    np.testing.assert_allclose(k.speed_rate_m_s2, 0., atol=1e-12)
    np.testing.assert_allclose(k.acceleration_magnitude_m_s2, 1., atol=.0001)


@pytest.mark.parametrize('t', [[0., 1., 1., 2.], [0., 1., .5, 1.5], [0., 1., 5., 6.]])
def test_no_differentiation_across_duplicate_reversed_or_large_intervals(t):
    np.testing.assert_allclose(differentiate(stamps(t), [0., 1., 100., 101.]), 1.)


def test_nan_segments_isolated_point_two_points_and_empty():
    result = differentiate(stamps([0, 1, 2, 3, 4]), [0., 1., np.nan, 9., np.inf])
    np.testing.assert_allclose(result[:2], 1.)
    assert np.isnan(result[2:]).all()
    assert np.isnan(differentiate(stamps([0]), [1.])).all()
    assert differentiate(stamps([]), []).size == 0


def test_vector_shape_and_gap_validation():
    with pytest.raises(ValueError):
        compute_kinematics(stamps([0, 1]), np.ones((2, 2)))
    with pytest.raises(ValueError):
        differentiate(stamps([0]), [0.], 0)
