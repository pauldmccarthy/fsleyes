/*
 * Functions for moving between 1D coordinates and 2D/3D coordinates.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */


/*
 * Converts a 3D coordinate to the equivalent 1D index.
 */
int unroll3D(vec3 indices, vec3 shape) {

     float flattened = indices.x + 
                       indices.y * shape.x + 
                       indices.z * shape.x * shape.y;

     return int(flattened);
}


/*
 * Converts a 1D index to the equivalent 3D coordinates.
 */
vec3 roll3D(int index, vec3 shape) {

    float stridex  = shape.x;
    float stridexy = shape.x * shape.y;

    float zidx = floor(index / stridexy);
    float zrem = mod(  index,  stridexy);
    float yidx = floor(zrem  / stridex);
    float yrem = mod(  zrem,   stridex);
    float xidx = yrem;

    return vec3(xidx, yidx, zidx);
}
