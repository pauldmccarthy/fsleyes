/**
 * Simple bounds test to determine whether the given voxel coordinates
 * are within the bounds specified by the given array/image shape.
 */
bool test_in_bounds(vec3 coords, vec3 shape) {

    /*
     * Don't render the fragment if it's outside the image space
     */
    if (coords.x < -0.51 || coords.x >= shape.x - 0.49 ||
        coords.y < -0.51 || coords.y >= shape.y - 0.49 ||
        coords.z < -0.51 || coords.z >= shape.z - 0.49) {

        return false;
    }

    return true;
}


vec3 _textest_ones  = vec3(1, 1, 1);
vec3 _textest_zeros = vec3(0, 0, 0);

/*
 * Tests whether the given texture coordinates are outside the
 * texture coordinate range.
 */
bool textest(vec3 coords) {
  return (!(any(greaterThan(coords, _textest_ones)) ||
            any(lessThan(   coords, _textest_zeros))));
}

bool textest(vec3 coords, float tol) {
  return (!(any(greaterThan(coords-tol, _textest_ones)) ||
            any(lessThan(   coords+tol, _textest_zeros))));
}
