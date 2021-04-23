/*
 * Simple edge-detection functions.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */

/* for single-channel 3D textures */ 
bool edge3D(sampler3D tex, vec3 coord, float val, float tol, vec3 offsets) {

  vec3 off;

  for (int i = 0; i < 3; i++) {

        if (offsets[i] <= 0)
            continue;

        off    = vec3(0, 0, 0);
        off[i] = offsets[i];

        float back  = texture3D(tex, coord + off).r;
        float front = texture3D(tex, coord - off).r;

        if (abs(val - back)  > tol ||
            abs(val - front) > tol) {
            return true;
        } 
    }

    return false;
}

/* for single-channel 2D textures */ 
bool edge2D(sampler2D tex, vec2 coord, float val, float tol, vec2 offsets) {

    vec2 off;

    for (int i = 0; i < 2; i++) {

        if (offsets[i] <= 0)
            continue;

        off    = vec2(0, 0);
        off[i] = offsets[i];

        float back  = texture2D(tex, coord + off).r;
        float front = texture2D(tex, coord - off).r;

        if (abs(val - back)  > tol ||
            abs(val - front) > tol) {
            return true;
        } 
    }

    return false;  
}


/* for multi-channel 2D textures */ 
bool edge2D(sampler2D tex, vec2 coord, vec4 val, vec4 tol, vec2 offsets) {

    vec2 off;

    for (int i = 0; i < 2; i++) {

        if (offsets[i] <= 0)
            continue;

        off    = vec2(0, 0);
        off[i] = offsets[i];

        vec4 back  = texture2D(tex, coord + off);
        vec4 front = texture2D(tex, coord - off);

        if (any(greaterThan(abs(val - back),  tol)) ||
            any(greaterThan(abs(val - front), tol))) {
            return true;
        } 
    }

    return false;  
}
