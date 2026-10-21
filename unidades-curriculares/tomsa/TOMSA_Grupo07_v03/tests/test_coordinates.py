import numpy as np
from scipy.spatial.transform import Rotation
from tomsa.coordinates import (WGS84_A, geodetic_to_ecef, geodetic_to_ned,
                                robot_to_world, world_to_robot)


def test_ecef_equator():
    np.testing.assert_allclose(geodetic_to_ecef(0, 0, 0), [WGS84_A, 0, 0], atol=1e-8)


def test_ned_origin_is_zero():
    np.testing.assert_allclose(geodetic_to_ned(41.45, -8.81, 55, 41.45, -8.81, 55),
                               [0, 0, 0], atol=1e-8)


def test_ned_directions():
    ref = (41.452, -8.813, 55.0)
    north = geodetic_to_ned(ref[0] + 0.00001, ref[1], ref[2], *ref)
    east = geodetic_to_ned(ref[0], ref[1] + 0.00001, ref[2], *ref)
    up = geodetic_to_ned(ref[0], ref[1], ref[2] + 10, *ref)
    assert north[0] > 1 and abs(north[1]) < 1e-4
    assert east[1] > .8 and abs(east[0]) < 1e-4
    np.testing.assert_allclose(up, [0, 0, -10], atol=1e-5)


def test_robot_local_yaw90_and_inverse():
    origin = np.array([12.0, 5.0, -2.0])
    point = origin + np.array([0.0, 10.0, 0.0])
    q = Rotation.from_euler('z', 90, degrees=True).as_quat()
    local = world_to_robot(point, origin, q)
    np.testing.assert_allclose(local, [10, 0, 0], atol=1e-12)
    np.testing.assert_allclose(robot_to_world(local, origin, q), point, atol=1e-12)


def test_distance_preserved():
    q = Rotation.from_euler('xyz', [25, -10, 70], degrees=True).as_quat()
    pts = np.array([[4, 5, 6], [11, 13, 8]], dtype=float)
    local = world_to_robot(pts, [2, -4, 1], q)
    np.testing.assert_allclose(np.linalg.norm(pts[1] - pts[0]),
                               np.linalg.norm(local[1] - local[0]), atol=1e-12)


def test_aer_cardinal_and_elevation():
    from tomsa.coordinates import ned_to_aer
    az, el, dist = ned_to_aer([0, 10, -10])
    np.testing.assert_allclose([az, el, dist], [90, 45, np.sqrt(200)], atol=1e-12)
    az, el, dist = ned_to_aer([10, 0, 0])
    np.testing.assert_allclose([az, el, dist], [0, 0, 10], atol=1e-12)
    az, el, dist = ned_to_aer([0, 0, 0])
    assert np.isnan(az) and np.isnan(el) and dist == 0


def test_aer_batch():
    from tomsa.coordinates import ned_to_aer
    az, el, dist = ned_to_aer(np.array([[10.,0.,0.], [0.,-10.,0.]]))
    np.testing.assert_allclose(az, [0,270], atol=1e-12)
    np.testing.assert_allclose(el, [0,0], atol=1e-12)
    np.testing.assert_allclose(dist, [10,10], atol=1e-12)
