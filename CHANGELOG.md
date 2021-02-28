# Changelog

## [v0.2.7](https://github.com/napari/magicgui/tree/v0.2.7) (2021-02-28)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.2.6...v0.2.7)

v0.2.7 is a minor feature & bugfix release including:

- parameter value persistence: use `@magicgui(persist=True)` to store the values in the GUI to disk when they are changed, and restore them when the GUI is recreated in a future session (#160).
- a preliminary Image widget `magicgui.widgets.Image`.  Requires `pip install magicgui[image]` to work (#140)
- adds a `widget_init` parameter to `magic_factory`... useful for connecting events and such after a factory creates a new widget instance (#159).
- fixes a bug when a parameter-less function is used with `call_button=True` (#149)
- fixes `FileEdit` used with directory mode
- fixes a bug in Range/SliceEdits


**Implemented enhancements:**

- Add a cache keyword to read parameter values from disk [\#152](https://github.com/napari/magicgui/issues/152)

**Fixed bugs:**

- Better error message on bad keyword argument to `magicgui` [\#165](https://github.com/napari/magicgui/issues/165)
- RangeEdit and SliceEdit behave unexpectedly [\#162](https://github.com/napari/magicgui/issues/162)
- "No module named numpy" [\#161](https://github.com/napari/magicgui/issues/161)
- FileEdit widget error with mode='d' [\#156](https://github.com/napari/magicgui/issues/156)
- Cannot connect event callbacks to MagicFactory [\#155](https://github.com/napari/magicgui/issues/155)
- Core dump error when running example napari parameter sweep [\#153](https://github.com/napari/magicgui/issues/153)
- decorating a function that uses `napari.viewer.add\_points` with magicgui generates a Shader compilation error [\#147](https://github.com/napari/magicgui/issues/147)
- vertical layout with no widgets error in `\_unify\_label\_widths` [\#146](https://github.com/napari/magicgui/issues/146)
- annotating an argument as magicgui.types.PathLike does not create a files widget [\#144](https://github.com/napari/magicgui/issues/144)
- Label option for boolean parameters has no effect [\#109](https://github.com/napari/magicgui/issues/109)

**Closed issues:**

- Contrib module [\#40](https://github.com/napari/magicgui/issues/40)

**Merged pull requests:**

- improve error message for bad kwargs [\#167](https://github.com/napari/magicgui/pull/167) ([tlambert03](https://github.com/tlambert03))
- fix range/slice edits [\#166](https://github.com/napari/magicgui/pull/166) ([tlambert03](https://github.com/tlambert03))
- Work without numpy [\#164](https://github.com/napari/magicgui/pull/164) ([tlambert03](https://github.com/tlambert03))
- Persist parameter values across sessions [\#160](https://github.com/napari/magicgui/pull/160) ([tlambert03](https://github.com/tlambert03))
- Add `widget\_init` parameter to `magic\_factory` [\#159](https://github.com/napari/magicgui/pull/159) ([tlambert03](https://github.com/tlambert03))
- Fix FileEdit with directory mode [\#158](https://github.com/napari/magicgui/pull/158) ([tlambert03](https://github.com/tlambert03))
- \[pre-commit.ci\] pre-commit autoupdate [\#157](https://github.com/napari/magicgui/pull/157) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Fix napari return annotations [\#154](https://github.com/napari/magicgui/pull/154) ([sofroniewn](https://github.com/sofroniewn))
- Allow `magicgui.types.PathLike` annotation [\#151](https://github.com/napari/magicgui/pull/151) ([tlambert03](https://github.com/tlambert03))
- allow label to be alias for text in button widgets [\#150](https://github.com/napari/magicgui/pull/150) ([tlambert03](https://github.com/tlambert03))
- fix function with no params and callbutton [\#149](https://github.com/napari/magicgui/pull/149) ([tlambert03](https://github.com/tlambert03))
- \[pre-commit.ci\] pre-commit autoupdate [\#148](https://github.com/napari/magicgui/pull/148) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Move return\_annotation from container to FunctionGui [\#143](https://github.com/napari/magicgui/pull/143) ([tlambert03](https://github.com/tlambert03))
- \[pre-commit.ci\] pre-commit autoupdate [\#142](https://github.com/napari/magicgui/pull/142) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Fix typesafety checks with numpy 1.20 [\#141](https://github.com/napari/magicgui/pull/141) ([tlambert03](https://github.com/tlambert03))
- Image widget [\#140](https://github.com/napari/magicgui/pull/140) ([tlambert03](https://github.com/tlambert03))
- Disable call button while function is running [\#139](https://github.com/napari/magicgui/pull/139) ([tlambert03](https://github.com/tlambert03))
- Remove pre 0.2.0 deprecation warnings [\#138](https://github.com/napari/magicgui/pull/138) ([tlambert03](https://github.com/tlambert03))
- update changelog [\#137](https://github.com/napari/magicgui/pull/137) ([tlambert03](https://github.com/tlambert03))
- \[pre-commit.ci\] pre-commit autoupdate [\#136](https://github.com/napari/magicgui/pull/136) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))

## [v0.2.6](https://github.com/napari/magicgui/tree/v0.2.6) (2021-01-25)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.2.5...v0.2.6)

v0.2.6 is a significant feature release, introducing a number of new widgets and APIs:

- New `Table` Widget allowing easy creation and modification of Table UIs using a variety of pure python types as input ([\#61](https://github.com/napari/magicgui/pull/61))
- Tooltips for each widget in a `@magicgui` are now automatically taken from docstrings (numpy, google, and sphinx-rst format accepted)([\#100](https://github.com/napari/magicgui/pull/100))
- New `ProgressBar` widget ([\#104](https://github.com/napari/magicgui/pull/104)) and `magicgui.tqdm` wrapper ([\#105](https://github.com/napari/magicgui/pull/105)) allow both manual and automatically-added progress bars to long-running iterator-based functions.  `magicgui.tqdm.tqdm` acts as a drop-in replacement for `tqdm.tqdm` that will fall back to the standard (console output) behavior if used outside of a magicgui function, or _inside_ of a magicgui widget that is not yet visible.
- New `MainWindow/MainFunctionGui` subclasses allow creating top level "application" windows, with a basic API for adding items to the application menubar ([\#110](https://github.com/napari/magicgui/pull/110)).
- The new `@magic_factory` decorator creates a *callable* that, when called, returns a `FunctionGui` instance (as opposed to `@magicgui` which immediately creates the `FunctionGui` instance.  Think of this as returning a "class" as opposed to returning an "instance":
   ```python
   @magic_factory(call_button=True)
   def my_factory(x: int, y = 'hi'):
       ...

   # can add to or override original factory arguments
   widget = my_factory(main_window=True)
   widget.show()
   ```
- "vertical" is now the default layout for `Containers` and magicgui widgets.

**Implemented enhancements:**

- Best way to add general docs and help menu? [\#107](https://github.com/napari/magicgui/issues/107)
- Tooltips [\#94](https://github.com/napari/magicgui/issues/94)
- Progress bar widget for long-running computations [\#25](https://github.com/napari/magicgui/issues/25)

**Fixed bugs:**

- Adding stretch to a widget's native layout causes a crash [\#111](https://github.com/napari/magicgui/issues/111)

**Closed issues:**

- Adding a stretch to the bottom of widgets [\#127](https://github.com/napari/magicgui/issues/127)
- make vertical layout default [\#121](https://github.com/napari/magicgui/issues/121)
- Proposal: don't instantiate widgets when no widget is defined for specific type [\#101](https://github.com/napari/magicgui/issues/101)

**Merged pull requests:**

- Add `magicgui.\*` objectName to qt widgets [\#134](https://github.com/napari/magicgui/pull/134) ([tlambert03](https://github.com/tlambert03))
- remove \_qt module [\#133](https://github.com/napari/magicgui/pull/133) ([tlambert03](https://github.com/tlambert03))
- Improve fallback behavior of tqdm iterator inside of \*hidden\* magicgui widget [\#131](https://github.com/napari/magicgui/pull/131) ([tlambert03](https://github.com/tlambert03))
- Improve issues with widget visibility [\#130](https://github.com/napari/magicgui/pull/130) ([tlambert03](https://github.com/tlambert03))
- add attribute error to `magicgui.\_\_getattr\_\_` [\#129](https://github.com/napari/magicgui/pull/129) ([tlambert03](https://github.com/tlambert03))
- Make `\_magicgui.pyi` stubs [\#126](https://github.com/napari/magicgui/pull/126) ([tlambert03](https://github.com/tlambert03))
- Fix `@magic\_factory` usage in local scopes [\#125](https://github.com/napari/magicgui/pull/125) ([tlambert03](https://github.com/tlambert03))
- Make vertical layout the default [\#124](https://github.com/napari/magicgui/pull/124) ([tlambert03](https://github.com/tlambert03))
- fix date topython [\#123](https://github.com/napari/magicgui/pull/123) ([tlambert03](https://github.com/tlambert03))
- Remove deprecated "result" param to `magicgui` [\#122](https://github.com/napari/magicgui/pull/122) ([tlambert03](https://github.com/tlambert03))
- Fix tooltips for multiple params names on one line [\#120](https://github.com/napari/magicgui/pull/120) ([tlambert03](https://github.com/tlambert03))
- Fix bug in tooltip parsing [\#119](https://github.com/napari/magicgui/pull/119) ([tlambert03](https://github.com/tlambert03))
- More docs for main\_window flag [\#118](https://github.com/napari/magicgui/pull/118) ([HagaiHargil](https://github.com/HagaiHargil))
- Magic factory [\#117](https://github.com/napari/magicgui/pull/117) ([tlambert03](https://github.com/tlambert03))
- Add more sizing options \(min/max width/height\) [\#116](https://github.com/napari/magicgui/pull/116) ([tlambert03](https://github.com/tlambert03))
- Move `FunctionGui` into widgets [\#115](https://github.com/napari/magicgui/pull/115) ([tlambert03](https://github.com/tlambert03))
- Split widget bases into files [\#114](https://github.com/napari/magicgui/pull/114) ([tlambert03](https://github.com/tlambert03))
- User internal model for `Container`, simplify `ContainerWidgetProtocol` [\#113](https://github.com/napari/magicgui/pull/113) ([tlambert03](https://github.com/tlambert03))
- setup.cfg updates [\#112](https://github.com/napari/magicgui/pull/112) ([tlambert03](https://github.com/tlambert03))
- Add `MainWindow` variant on `Container`, and `MainFunctionGui` [\#110](https://github.com/napari/magicgui/pull/110) ([tlambert03](https://github.com/tlambert03))
- Parse the entire docstring for the tooltip [\#108](https://github.com/napari/magicgui/pull/108) ([HagaiHargil](https://github.com/HagaiHargil))
- improved labeled widgets [\#106](https://github.com/napari/magicgui/pull/106) ([tlambert03](https://github.com/tlambert03))
- Progress bar tqdm wrapper, and manual control [\#105](https://github.com/napari/magicgui/pull/105) ([tlambert03](https://github.com/tlambert03))
- Add ProgressBar widget [\#104](https://github.com/napari/magicgui/pull/104) ([tlambert03](https://github.com/tlambert03))
- Use \(hidden\) EmptyWidget for unrecognized types [\#103](https://github.com/napari/magicgui/pull/103) ([tlambert03](https://github.com/tlambert03))
- Add manual and docstring-parsed tooltips [\#100](https://github.com/napari/magicgui/pull/100) ([tlambert03](https://github.com/tlambert03))
- Add Table Widget [\#61](https://github.com/napari/magicgui/pull/61) ([tlambert03](https://github.com/tlambert03))

## [v0.2.5](https://github.com/napari/magicgui/tree/v0.2.5) (2021-01-13)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.2.4...v0.2.5)

v0.2.5 greatly improves support for binding a value or a callback to a function parameter, and fixes a bug in recursively updating categorical widgets nested deeply inside of a container.

**Merged pull requests:**

- Fix reset\_choices recursion [\#96](https://github.com/napari/magicgui/pull/96) ([tlambert03](https://github.com/tlambert03))
- better bound values [\#95](https://github.com/napari/magicgui/pull/95) ([tlambert03](https://github.com/tlambert03))

## [v0.2.4](https://github.com/napari/magicgui/tree/v0.2.4) (2021-01-12)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.2.3...v0.2.4)

**Merged pull requests:**

- Extend combobox api with set\_choice, get\_choice, del\_choice [\#92](https://github.com/napari/magicgui/pull/92) ([tlambert03](https://github.com/tlambert03))

## [v0.2.3](https://github.com/napari/magicgui/tree/v0.2.3) (2021-01-08)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.2.2...v0.2.3)

v0.2.3 adds two new widgets `DateEdit` and `TimeEdit` (for `datetime.date` and `datetime.time` types respectively), in addition to the existing `DateTimeEdit` widget.  It also continues to improve warnings and deprecation messages from the v0.2.0 release.

**Fixed bugs:**

- magicgui.widgets.CategoricalWidget not found in magicgui 0.2.1 [\#81](https://github.com/napari/magicgui/issues/81)

**Closed issues:**

- QTimeEdit widgets [\#78](https://github.com/napari/magicgui/issues/78)

**Merged pull requests:**

- Fix ComboBox with unhashable choice data [\#89](https://github.com/napari/magicgui/pull/89) ([tlambert03](https://github.com/tlambert03))
- add pyupgrade pre-commit hook [\#88](https://github.com/napari/magicgui/pull/88) ([tlambert03](https://github.com/tlambert03))
- add call count to function gui [\#86](https://github.com/napari/magicgui/pull/86) ([tlambert03](https://github.com/tlambert03))
- Add more examples \(chaining, self-reference, and choices\) [\#85](https://github.com/napari/magicgui/pull/85) ([tlambert03](https://github.com/tlambert03))
- Add date and time widgets [\#84](https://github.com/napari/magicgui/pull/84) ([tlambert03](https://github.com/tlambert03))
- Clarify choices callable deprecation warning [\#83](https://github.com/napari/magicgui/pull/83) ([tlambert03](https://github.com/tlambert03))
- Convert maximum/minimum kwargs to max/min and warn [\#82](https://github.com/napari/magicgui/pull/82) ([tlambert03](https://github.com/tlambert03))
- \[pre-commit.ci\] pre-commit autoupdate [\#80](https://github.com/napari/magicgui/pull/80) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))

## [v0.2.2](https://github.com/napari/magicgui/tree/v0.2.2) (2021-01-02)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.2.1...v0.2.2)

**Merged pull requests:**

- hotfix for signature inspection exception [\#79](https://github.com/napari/magicgui/pull/79) ([tlambert03](https://github.com/tlambert03))
- remove orientation method from supportsOrientation [\#77](https://github.com/napari/magicgui/pull/77) ([tlambert03](https://github.com/tlambert03))
- Better error on incorrect protocol [\#76](https://github.com/napari/magicgui/pull/76) ([tlambert03](https://github.com/tlambert03))
- save application instance [\#75](https://github.com/napari/magicgui/pull/75) ([tlambert03](https://github.com/tlambert03))

## [v0.2.1](https://github.com/napari/magicgui/tree/v0.2.1) (2020-12-29)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.2.0...v0.2.1)

v0.2.1 fixes some issues with the 0.2.0 release.  `ForwardRef` annotations are now resolved automatically on both parameter and return type annotations.  And the `orientation` parameter on `Container` widgets (such as those returned by the `magicgui` decorator) has been renamed back to `layout` as in <v0.2.0.  Test coverage is also improved.

**Fixed bugs:**

- napari examples in the docs are broken [\#72](https://github.com/napari/magicgui/issues/72)
- Functions without arguments are not finding napari parent widgets [\#64](https://github.com/napari/magicgui/issues/64)
- "Layout" parameter doesn't work anymore in recent dev version [\#54](https://github.com/napari/magicgui/issues/54)

**Closed issues:**

- Should we permanently resolve ForwardRef type annotations? [\#65](https://github.com/napari/magicgui/issues/65)
- Need consensus on "layout" vs "orientation" [\#63](https://github.com/napari/magicgui/issues/63)

**Merged pull requests:**

- Resolve ForwardRefs on return annotations [\#73](https://github.com/napari/magicgui/pull/73) ([tlambert03](https://github.com/tlambert03))
- \[pre-commit.ci\] pre-commit autoupdate [\#71](https://github.com/napari/magicgui/pull/71) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Improve test coverage [\#70](https://github.com/napari/magicgui/pull/70) ([tlambert03](https://github.com/tlambert03))
- Fix parent\_changed signal emission [\#69](https://github.com/napari/magicgui/pull/69) ([tlambert03](https://github.com/tlambert03))
- Add tests for docs and examples [\#68](https://github.com/napari/magicgui/pull/68) ([tlambert03](https://github.com/tlambert03))
- Change "orientation" on containers to "layout" [\#67](https://github.com/napari/magicgui/pull/67) ([tlambert03](https://github.com/tlambert03))
- resolve ForwardRef on widget.annotation [\#66](https://github.com/napari/magicgui/pull/66) ([tlambert03](https://github.com/tlambert03))

## [v0.2.0](https://github.com/napari/magicgui/tree/v0.2.0) (2020-12-26)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.1.6...v0.2.0)

v0.2.0 includes a complete rewrite of magicgui.  The primary goals were as follows:
- make a clean separation between the Qt backend and the end-use API, clarifying the interface that a backend must implement in order to work with magicgui
- create a "direct API" that enables procedural widget creation, with the potential for subclassing and custom widget creation
- create a more direct link between an individual widget and an `inspect.Parameter` object, and a collection or layout of widgets and an `inspect.Signature` object.

See PR #43  for full details of the rewrite.

**Deprecations and possible breaking changes!**

Some of the API has been deprecated or changed, though an attempt was made to make the pre-0.2.0 API still work (with warnings).  Please see the [v0.2.0 migration guide](https://napari.org/magicgui/api/v0_2_0.html) for details.

Lastly, we have new documentation, using the amazing [jupyter-book](https://jupyterbook.org/intro.html) project!  Note the new url at https://napari.org/magicgui

**Implemented enhancements:**

- Provide more direct "autowidget generation" without requiring function body. [\#7](https://github.com/napari/magicgui/issues/7)

**Fixed bugs:**

- call\_button not responding [\#44](https://github.com/napari/magicgui/issues/44)
- Removal of docks: are widgets singletons? [\#28](https://github.com/napari/magicgui/issues/28)

**Closed issues:**

- Enable magicgui decorator on class member functions [\#53](https://github.com/napari/magicgui/issues/53)
- Recognize widget types as strings [\#47](https://github.com/napari/magicgui/issues/47)
- Recognize napari layer types as strings [\#46](https://github.com/napari/magicgui/issues/46)
- Widget label editable  [\#45](https://github.com/napari/magicgui/issues/45)
- Add support for Annotated type [\#34](https://github.com/napari/magicgui/issues/34)
- Pull signature parsing code from MagicGuiBase [\#33](https://github.com/napari/magicgui/issues/33)

**Merged pull requests:**

- API cleanup and unify with ipywidgets \(a little\) [\#60](https://github.com/napari/magicgui/pull/60) ([tlambert03](https://github.com/tlambert03))
- Labels update [\#59](https://github.com/napari/magicgui/pull/59) ([tlambert03](https://github.com/tlambert03))
- New documentation [\#58](https://github.com/napari/magicgui/pull/58) ([tlambert03](https://github.com/tlambert03))
- Corrected usage / example code of parameter 'choices' [\#57](https://github.com/napari/magicgui/pull/57) ([haesleinhuepf](https://github.com/haesleinhuepf))
- Enable decorator to be used on methods [\#56](https://github.com/napari/magicgui/pull/56) ([tlambert03](https://github.com/tlambert03))
- add application\_name variable [\#55](https://github.com/napari/magicgui/pull/55) ([tlambert03](https://github.com/tlambert03))
- add support for ForwardRef [\#52](https://github.com/napari/magicgui/pull/52) ([tlambert03](https://github.com/tlambert03))
- test on py39 [\#50](https://github.com/napari/magicgui/pull/50) ([tlambert03](https://github.com/tlambert03))
- Add a "display\_name" option to modify a widget's label \(\#45\) [\#48](https://github.com/napari/magicgui/pull/48) ([HagaiHargil](https://github.com/HagaiHargil))
- rewrite: proper widget protocols & signature objects [\#43](https://github.com/napari/magicgui/pull/43) ([tlambert03](https://github.com/tlambert03))
- Drop support for python 3.6 [\#42](https://github.com/napari/magicgui/pull/42) ([tlambert03](https://github.com/tlambert03))
- Add \(slightly\) strict mypy checking [\#41](https://github.com/napari/magicgui/pull/41) ([tlambert03](https://github.com/tlambert03))

## [v0.1.6](https://github.com/napari/magicgui/tree/v0.1.6) (2020-07-23)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.1.6rc0...v0.1.6)

## [v0.1.6rc0](https://github.com/napari/magicgui/tree/v0.1.6rc0) (2020-07-23)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.1.5...v0.1.6rc0)

**Implemented enhancements:**

- Use eval'd text box as fallback when type inference fails [\#29](https://github.com/napari/magicgui/issues/29)

**Closed issues:**

- conda recipe [\#21](https://github.com/napari/magicgui/issues/21)
- Feature request: support for QFileDialog \(file and directory choosers\) [\#20](https://github.com/napari/magicgui/issues/20)
- Unable to visualize QBoxlayout nor QTable  [\#12](https://github.com/napari/magicgui/issues/12)

**Merged pull requests:**

- Add flake8-docstrings to dev requirements [\#39](https://github.com/napari/magicgui/pull/39) ([GenevieveBuckley](https://github.com/GenevieveBuckley))
- Add a logarithmic scale slider class [\#38](https://github.com/napari/magicgui/pull/38) ([GenevieveBuckley](https://github.com/GenevieveBuckley))
- Fix napari\_param\_sweep.py example by updating QDoubleSlider import [\#37](https://github.com/napari/magicgui/pull/37) ([GenevieveBuckley](https://github.com/GenevieveBuckley))
- Widget demo example script [\#36](https://github.com/napari/magicgui/pull/36) ([GenevieveBuckley](https://github.com/GenevieveBuckley))
- Reorganize \_qt module [\#32](https://github.com/napari/magicgui/pull/32) ([tlambert03](https://github.com/tlambert03))
- add literal eval fallback widget [\#31](https://github.com/napari/magicgui/pull/31) ([tlambert03](https://github.com/tlambert03))
- support Sequence\[Path\] [\#27](https://github.com/napari/magicgui/pull/27) ([tlambert03](https://github.com/tlambert03))
- Make sure black reformatting is an error on CI [\#26](https://github.com/napari/magicgui/pull/26) ([tlambert03](https://github.com/tlambert03))
- Pin Linux Qt \<5.15 [\#24](https://github.com/napari/magicgui/pull/24) ([tlambert03](https://github.com/tlambert03))
- Filedialog widget for magicgui [\#23](https://github.com/napari/magicgui/pull/23) ([GenevieveBuckley](https://github.com/GenevieveBuckley))
- Add datetime to type2widget function [\#22](https://github.com/napari/magicgui/pull/22) ([GenevieveBuckley](https://github.com/GenevieveBuckley))
- Must import scikit-image modules specifically [\#18](https://github.com/napari/magicgui/pull/18) ([GenevieveBuckley](https://github.com/GenevieveBuckley))

## [v0.1.5](https://github.com/napari/magicgui/tree/v0.1.5) (2020-05-24)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.1.4...v0.1.5)

**Fixed bugs:**

- Error running examples [\#6](https://github.com/napari/magicgui/issues/6)

**Closed issues:**

- Automagically add labels per field [\#13](https://github.com/napari/magicgui/issues/13)

**Merged pull requests:**

- Add the ability to hide a widget [\#17](https://github.com/napari/magicgui/pull/17) ([tlambert03](https://github.com/tlambert03))

## [v0.1.4](https://github.com/napari/magicgui/tree/v0.1.4) (2020-05-19)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.1.3...v0.1.4)

**Merged pull requests:**

- Update ci, version with setuptools\_scm [\#15](https://github.com/napari/magicgui/pull/15) ([tlambert03](https://github.com/tlambert03))
- Initial support for labels [\#14](https://github.com/napari/magicgui/pull/14) ([tlambert03](https://github.com/tlambert03))

## [v0.1.3](https://github.com/napari/magicgui/tree/v0.1.3) (2020-05-04)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.1.2...v0.1.3)

**Merged pull requests:**

- pyright -\> mypy [\#11](https://github.com/napari/magicgui/pull/11) ([tlambert03](https://github.com/tlambert03))
- Update docs [\#10](https://github.com/napari/magicgui/pull/10) ([tlambert03](https://github.com/tlambert03))
- update param sweep example [\#8](https://github.com/napari/magicgui/pull/8) ([tlambert03](https://github.com/tlambert03))

## [v0.1.2](https://github.com/napari/magicgui/tree/v0.1.2) (2020-03-06)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.1.1...v0.1.2)

**Closed issues:**

- Register callbacks on return types [\#3](https://github.com/napari/magicgui/issues/3)

**Merged pull requests:**

- fix call\_button press for pyqt5 [\#5](https://github.com/napari/magicgui/pull/5) ([tlambert03](https://github.com/tlambert03))
- Register callbacks for return annotations [\#4](https://github.com/napari/magicgui/pull/4) ([tlambert03](https://github.com/tlambert03))

## [v0.1.1](https://github.com/napari/magicgui/tree/v0.1.1) (2020-02-19)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.1.0...v0.1.1)

**Merged pull requests:**

- split out deploy [\#2](https://github.com/napari/magicgui/pull/2) ([tlambert03](https://github.com/tlambert03))

## [v0.1.0](https://github.com/napari/magicgui/tree/v0.1.0) (2020-02-18)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.0.8...v0.1.0)

**Merged pull requests:**

- playing with travis [\#1](https://github.com/napari/magicgui/pull/1) ([tlambert03](https://github.com/tlambert03))

## [v0.0.8](https://github.com/napari/magicgui/tree/v0.0.8) (2020-02-11)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.0.7...v0.0.8)

## [v0.0.7](https://github.com/napari/magicgui/tree/v0.0.7) (2020-02-09)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.0.6...v0.0.7)

## [v0.0.6](https://github.com/napari/magicgui/tree/v0.0.6) (2020-02-09)

[Full Changelog](https://github.com/napari/magicgui/compare/7fefc99d72fb94cc210cd862248ea75dc9c97d16...v0.0.6)



\* *This Changelog was automatically generated by [github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)*
