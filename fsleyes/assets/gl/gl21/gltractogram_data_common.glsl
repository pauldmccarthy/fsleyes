/*
 * Function used by gltractogram fragment shaders, for
 * converting a data value into a RGBA colour according
 * to TractogramOpts/ColourMapOpts settings
 */

/* Positive/negative colour maps */
uniform sampler1D cmap;
uniform sampler1D negCmap;
uniform bool      useNegCmap;

/* Transform from data values into colour map texture coordinates */
uniform float     cmapScale;
uniform float     cmapOffset;

/*
 * Clipping. The sameData flag is set if the clipping data is the same
 * as the colouring data.
 */
uniform bool      sameData;
uniform bool      invertClip;
uniform float     clipLow;
uniform float     clipHigh;

/* Modulate transparency by vertex data intensity */
uniform bool      modulateAlpha;
uniform float     modScale;
uniform float     modOffset;


vec4 generateColour(float data, float clipData) {
  vec4  colour;
  float texCoord;
  float clipValue;
  bool  negative;
  bool  clip;

  // vertex data is nan
  if (data != data) {
      discard;
  }

  negative = useNegCmap && data < 0;

  if (negative) { data     = -data; }
  if (sameData) { clipData =  data; }

  clip = (!invertClip && (clipData <= clipLow || clipData >= clipHigh)) ||
         ( invertClip && (clipData >= clipLow && clipData <= clipHigh));

  if (clip) {
    discard;
  }

  texCoord = data * cmapScale + cmapOffset;

  if (negative) colour = texture1D(negCmap, texCoord);
  else          colour = texture1D(cmap,    texCoord);

  if (modulateAlpha) {
    colour.a = colour.a * data * modScale + modOffset;
  }

  return colour;
}
