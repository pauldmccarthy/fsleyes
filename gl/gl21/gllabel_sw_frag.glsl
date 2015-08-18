#version 120

uniform sampler3D imageTexture;
uniform sampler1D lutTexture;
uniform mat4      voxValXform;
uniform vec3      imageShape;
uniform float     numLabels;
varying vec3      fragTexCoord;


void main(void) {

    float voxValue = texture3D(imageTexture, fragTexCoord).r;
    float lutCoord = ((voxValXform * vec4(voxValue, 0, 0, 1)).x + 0.5) / numLabels;
    
    gl_FragColor = texture1D(lutTexture, lutCoord);
}
