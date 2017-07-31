/*
 * Data and function definitions used by the 2D/3D GLMesh data fragment
 * shaders.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */

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


/* Vertex data value */
varying float     fragVertexData;


vec4 glmesh_data_colour() {

  vec4  result;
  float vertexData;
  float texCoord;
  float clipValue;
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
      result = flatColour;
    }
  }
  else {

    texCoord = (cmapXform * vec4(vertexData, 0, 0, 1)).x;

    if (negative) result = texture1D(negCmap, texCoord);
    else          result = texture1D(cmap,    texCoord);
  }

  return result;
}
