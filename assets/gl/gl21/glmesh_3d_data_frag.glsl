/*
 * Fragment shader used for drawing GLMesh outlines.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

#pragma include glmesh_3d_lighting.glsl

/* Colour map to use */
uniform sampler1D cmap;

/* Colour map to use for negative values, if useNegCmap is true */
uniform sampler1D negCmap;


/* Transformation from data values to colour map texture coordinates */
uniform mat4      cmapXform;

/* Use negCmap for negative values */
uniform bool      useNegCmap;

/* Invert the clipping range */
uniform bool      invertClip;

/* Clip values <= this value */
uniform float     clipLow;

/* Clip values >= this value  */
uniform float     clipHigh;

/* Control whether clipped fragments are discarded (true), or
whether they are drawn in the flatColour (false).
*/
uniform bool      discardClipped;

/* Colour to use when discardClipped is false, and a fragment is clipped. */
uniform vec4      flatColour;

uniform bool lighting;
uniform vec3 lightPos;
varying vec3 fragVertex;
varying vec3 fragNormal;

/* Vertex data value */
varying float     fragVertexData;


void main(void) {

  float vertexData;
  float texCoord;
  float clipValue;
  vec4  finalColour;
  bool  negative;
  bool  clip;

  negative = useNegCmap && fragVertexData < 0;

  if (negative) vertexData = -fragVertexData;
  else          vertexData =  fragVertexData;

  clip = (!invertClip && (vertexData <= clipLow || vertexData >= clipHigh)) ||
         ( invertClip && (vertexData >= clipLow && vertexData <= clipHigh));

  if (clip) {
    if (discardClipped) {
      discard;
    }
    else {
      finalColour = flatColour;
    }
  }
  else {

    texCoord = (cmapXform * vec4(vertexData, 0, 0, 1)).x;

    if (negative) finalColour = texture1D(negCmap, texCoord);
    else          finalColour = texture1D(cmap,    texCoord);
  }

  if (lighting) {

    finalColour.rgb = mesh_lighting(fragVertex,
                                    fragNormal,
                                    lightPos,
                                    finalColour.rgb);
  }

  gl_FragColor = finalColour;
}
