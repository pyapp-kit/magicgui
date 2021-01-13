# Changelog

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
