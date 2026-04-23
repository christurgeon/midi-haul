// Ambient declarations for html-midi-player custom elements
// eslint-disable-next-line @typescript-eslint/no-namespace
declare namespace React {
  namespace JSX {
    interface IntrinsicElements {
      "midi-player": React.DetailedHTMLProps<
        React.HTMLAttributes<HTMLElement> & {
          src?: string;
          "sound-font"?: string | boolean;
          loop?: boolean;
          ref?: React.Ref<HTMLElement>;
        },
        HTMLElement
      >;
      "midi-visualizer": React.DetailedHTMLProps<
        React.HTMLAttributes<HTMLElement> & {
          src?: string;
          type?: "piano-roll" | "staff";
          ref?: React.Ref<HTMLElement>;
        },
        HTMLElement
      >;
    }
  }
}
