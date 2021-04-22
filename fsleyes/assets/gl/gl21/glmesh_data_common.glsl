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
uniform mat4 cmapXform;

/* Use negCmap for negative values */
uniform bool useNegCmap;

/* Invert the clipping range */
uniform bool invertClip;

/* Clip values <= this value */
uniform float clipLow;

/* Clip values >= this value  */
uniform float clipHigh;

/*
 * Control whether clipped fragments are discarded (true), or
 * whether they are drawn in the flatColour (false).
 */
uniform bool discardClipped;

/* Colour to use when discardClipped is false, and a fragment is clipped. */
uniform vec4 flatColour;

/* Modulate fragment opacity by the vertex data intensity.  */
uniform bool modulateAlpha;

/* Scale/offset to apply to alpha modulation value.  */
uniform float modScale;
uniform float modOffset;

/* Vertex data value */
varying float fragVertexData;

/* Alpha modulation data value */
varying float fragModulateData;


vec4 glmesh_data_colour() {

  vec4  result;
  float vertexData;
  float texCoord;
  float clipValue;
  float modValue;
  bool  negative;
  bool  clip;

  // vertex data is nan
  if (fragVertexData != fragVertexData) {
    if (discardClipped) {
      discard;
    }
    else {
      result = flatColour;
    }
  }

  else {
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
  }

  /*
   * Rather than modulating the opacity, we
   * interpolate between the data colour and
   * the flat colour according to the modalpha
   * value
   */
  if (modulateAlpha) {
    modValue   = clamp(fragModulateData * modScale + modOffset, 0, 1);
    result.rgb = mix(flatColour.rgb, result.rgb, modValue);
  }

  return result;
}
