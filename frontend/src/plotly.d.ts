// The cartesian-only Plotly bundle ships without types, so reuse @types/plotly.js.
declare module 'plotly.js-cartesian-dist-min' {
  import * as Plotly from 'plotly.js'
  export default Plotly
}
