/*
 * Vertex shader for rendering GLTractogram instances.
 */
#version 120


attribute vec3 vertex;


void main(void) {

  gl_Position = gl_ModelViewProjectionMatrix *
                vec4(vertex, 1);
}
