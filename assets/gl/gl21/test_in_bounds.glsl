/**
 * Simple bounds test to determine whether the given voxel coordinates
 * are within the bounds specified by the given array/image shape.
 */
bool test_in_bounds(inout vec3 coords, vec3 shape) {

    /*
     * Don't render the fragment if it's outside the image space
     */
    if (coords.x < -0.01 || coords.x >= shape.x + 0.01 ||
        coords.y < -0.01 || coords.y >= shape.y + 0.01 ||
        coords.z < -0.01 || coords.z >= shape.z + 0.01) {
        
        return false;
    }

    return true;
}