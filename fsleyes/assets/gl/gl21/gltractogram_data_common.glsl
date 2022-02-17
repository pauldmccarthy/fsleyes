/* Positive/negative colour maps */
uniform sampler1D cmap;
uniform sampler1D negCmap;
uniform bool      useNegCmap;

/* Transform from data values into colour map texture coordinates */
uniform float     cmapScale;
uniform float     cmapOffset;

/* Clipping */
uniform bool      invertClip;
uniform float     clipLow;
uniform float     clipHigh;

/* Modulate transparency by vertex data intensity */
uniform bool      modulateAlpha;
uniform float     modScale;
uniform float     modOffset;


/*
 * Function shared by gltractogram_vertex_data_frag.glsl and
 * gltractogram_image_data_frag.glsl, for generating a colour
 * from a data value.
 */
vec4 generateColour(float data) {
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

  if (negative) {
    data = -data;
  }

  clip = (!invertClip && (data <= clipLow || data >= clipHigh)) ||
         ( invertClip && (data >= clipLow && data <= clipHigh));

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
