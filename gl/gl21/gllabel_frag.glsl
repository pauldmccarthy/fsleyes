#version 120

#pragma include edge.glsl
#pragma include spline_interp.glsl
#pragma include test_in_bounds.glsl

uniform sampler3D imageTexture;

uniform sampler1D lutTexture;

uniform mat4      voxValXform;

uniform vec3      imageShape;

uniform float     numLabels;

uniform bool      useSpline;

uniform bool      outline;

uniform vec3      outlineOffsets;

varying vec3      fragVoxCoord;

varying vec3      fragTexCoord;


void main(void) {

    vec3 voxCoord = fragVoxCoord;

    if (!test_in_bounds(voxCoord, imageShape)) {
        
        gl_FragColor = vec4(0, 0, 0, 0);
        return;
    }

    float voxValue;
    voxValue = texture3D(imageTexture, fragTexCoord).r;

    float lutCoord = ((voxValXform * vec4(voxValue, 0, 0, 1)).x + 0.5) / numLabels;

    if (lutCoord < 0 || lutCoord > 1) {
        gl_FragColor.a = 0.0;
        return;
    }
    
    vec4 colour = texture1D(lutTexture, lutCoord);

    float tol    = 0.001 / numLabels;
    bool  isEdge = edge3D(imageTexture, fragTexCoord, voxValue, tol, outlineOffsets);

    /* 
     * I want the fragment to be filled if outlines
     * are enabled, and the fragment lies on an edge,
     * or if outlines are disabled and the fragment
     * does not lie on an edge. The corresponding
     * boolean logic:
     * 
     *     (isEdge && outline) || !(isEdge || outline);
     *
     * is a negated exclusive or, which reduces
     * down to a simple equality test ...
     */
    if (isEdge == outline) gl_FragColor   = colour;
    else                   gl_FragColor.a = 0.0;
}
