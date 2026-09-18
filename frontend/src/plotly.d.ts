// "plotly.js-cartesian-dist-min" is a pre-built Plotly bundle with just the
// cartesian chart types (box, heatmap, scatter...), far smaller than full
// Plotly. It ships without its own types, so reuse the ones from @types/plotly.js.
declare module 'plotly.js-cartesian-dist-min' {
  import * as Plotly from 'plotly.js'
  export default Plotly
}
