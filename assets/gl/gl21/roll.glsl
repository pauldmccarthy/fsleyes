/*
 *
 */


int unroll3D(vec3 indices, vec3 shape) {

     float flattened = indices.x + 
                       indices.y * shape.x + 
                       indices.z * shape.x * shape.y;

     return int(flattened);
}


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
