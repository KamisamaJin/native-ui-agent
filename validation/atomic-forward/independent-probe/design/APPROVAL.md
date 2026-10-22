# Neutral design fixed before implementation

This independent probe context selected the design without seeing root implementation plans, prior trial results or future business studies. The same context will implement it; hashes do not establish separate human design authorship.

The component paints an opaque light canvas and a separate opaque empty accent band. Both regions are component-owned. The observer paints only the surrounding host; system status and host controls have no component color obligation. Canvas sampling uses the leftmost inner strip, outside padded content. Band sampling uses its empty central area. Neither sampling zone contains glyphs, gradients or transparency.

A vertical component uses 20 native-unit inner padding, 16-unit spacing, a 64-unit band, a title, body and an Acknowledge action. Title/body wrap naturally without a fixed text height or line cap. Text ink is dark #202124. On iOS use native title2/body; Android uses 22sp semibold/17sp body. All regions have square edges. A tap emits acknowledged and changes no model. The caller replaces title, body and both colors in the still-attached component; replacement emits no callback.

Normal: offered width390, light, ltr, large iOS Dynamic Type / Android fontScale1.0. Narrow/large: offered width260, light, ltr, accessibility3 / fontScale1.7. iOS host content width is offered width minus32; Android actual viewport is checked after capture. No physical Android touch, app navigation, keyboard, lifecycle or full style-tree claim is planned.

The typed reference and contract fix every expectation and original action route. Policy and lock digests will be recorded separately before component source is written.
