# Changelog

## [0.6.0](https://github.com/napari/magicgui/tree/0.6.0) (2022-10-26)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.6.0rc2...0.6.0)

**Merged pull requests:**

- docs: add doi to readme [\#479](https://github.com/napari/magicgui/pull/479) ([tlambert03](https://github.com/tlambert03))

## [v0.6.0rc2](https://github.com/napari/magicgui/tree/v0.6.0rc2) (2022-10-25)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.6.0rc1...v0.6.0rc2)

**Merged pull requests:**

- \[pre-commit.ci\] pre-commit autoupdate [\#477](https://github.com/napari/magicgui/pull/477) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Enable option to raise excpetion if magicgui cannot determine widget for provided value/annotation [\#476](https://github.com/napari/magicgui/pull/476) ([Czaki](https://github.com/Czaki))
- docs: fix word in slice edit docs [\#472](https://github.com/napari/magicgui/pull/472) ([tlambert03](https://github.com/tlambert03))

## [v0.6.0rc1](https://github.com/napari/magicgui/tree/v0.6.0rc1) (2022-10-22)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.6.0rc0...v0.6.0rc1)

**Implemented enhancements:**

- feat: add context manager for register\_type [\#470](https://github.com/napari/magicgui/pull/470) ([tlambert03](https://github.com/tlambert03))
- feat: click on button return [\#468](https://github.com/napari/magicgui/pull/468) ([tlambert03](https://github.com/tlambert03))

**Fixed bugs:**

- fix: Fix persist on magicgui method decorator [\#469](https://github.com/napari/magicgui/pull/469) ([tlambert03](https://github.com/tlambert03))
- fix: handle case of bad parameter cache file read [\#467](https://github.com/napari/magicgui/pull/467) ([tlambert03](https://github.com/tlambert03))
- use math.ceil to ensure get\_text\_width returns int [\#465](https://github.com/napari/magicgui/pull/465) ([psobolewskiPhD](https://github.com/psobolewskiPhD))
- Fix ipynb PushButton [\#464](https://github.com/napari/magicgui/pull/464) ([hanjinliu](https://github.com/hanjinliu))

**Merged pull requests:**

- docs: changelog v0.6.0rc1 [\#471](https://github.com/napari/magicgui/pull/471) ([tlambert03](https://github.com/tlambert03))

## [v0.6.0rc0](https://github.com/napari/magicgui/tree/v0.6.0rc0) (2022-10-21)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.5.1...v0.6.0rc0)

**Implemented enhancements:**

- Support `Literal` type [\#458](https://github.com/napari/magicgui/pull/458) ([hanjinliu](https://github.com/hanjinliu))
- feat: add range slider \(take 2\) [\#455](https://github.com/napari/magicgui/pull/455) ([tlambert03](https://github.com/tlambert03))
- feat: Pass parent to backend widget [\#440](https://github.com/napari/magicgui/pull/440) ([tlambert03](https://github.com/tlambert03))
- Add ipywidgets backend [\#87](https://github.com/napari/magicgui/pull/87) ([tlambert03](https://github.com/tlambert03))

**Fixed bugs:**

- fix: fix deprecation warning from matplotib about accessing colormaps from mpl.cm [\#451](https://github.com/napari/magicgui/pull/451) ([tlambert03](https://github.com/tlambert03))
- Fix FunctionGui behavior as a class method [\#443](https://github.com/napari/magicgui/pull/443) ([hanjinliu](https://github.com/hanjinliu))
- Expose QScrollArea as native widget [\#429](https://github.com/napari/magicgui/pull/429) ([dstansby](https://github.com/dstansby))
- Turn off adaptive step if "step" option is given [\#425](https://github.com/napari/magicgui/pull/425) ([hanjinliu](https://github.com/hanjinliu))

**Tests & CI:**

- tests: add test for magic-class [\#447](https://github.com/napari/magicgui/pull/447) ([tlambert03](https://github.com/tlambert03))
- test: change pytest testing plugin [\#438](https://github.com/napari/magicgui/pull/438) ([tlambert03](https://github.com/tlambert03))

**Documentation:**

- docs: changelog v0.6.0 [\#462](https://github.com/napari/magicgui/pull/462) ([tlambert03](https://github.com/tlambert03))
- Fix links in documentation [\#433](https://github.com/napari/magicgui/pull/433) ([Czaki](https://github.com/Czaki))
- fix docs build [\#428](https://github.com/napari/magicgui/pull/428) ([tlambert03](https://github.com/tlambert03))
- Bump jupyter-book to 0.12.x [\#427](https://github.com/napari/magicgui/pull/427) ([dstansby](https://github.com/dstansby))

**Merged pull requests:**

- build: pin pyside6 extra [\#460](https://github.com/napari/magicgui/pull/460) ([tlambert03](https://github.com/tlambert03))

## [v0.5.1](https://github.com/napari/magicgui/tree/v0.5.1) (2022-06-14)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.5.0...v0.5.1)

**Fixed bugs:**

- Emit signal only if value of caterogical widget changed [\#422](https://github.com/napari/magicgui/pull/422) ([Czaki](https://github.com/Czaki))

**Merged pull requests:**

- add changelog for v0.5.1 [\#423](https://github.com/napari/magicgui/pull/423) ([tlambert03](https://github.com/tlambert03))

## [v0.5.0](https://github.com/napari/magicgui/tree/v0.5.0) (2022-06-13)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.4.0...v0.5.0)

**Implemented enhancements:**

- feat: add request\_values convenience, shows modal dialog to request values [\#416](https://github.com/napari/magicgui/pull/416) ([tlambert03](https://github.com/tlambert03))
- Change to use adaptive step is SpinBox and FloatSpinBox [\#403](https://github.com/napari/magicgui/pull/403) ([Czaki](https://github.com/Czaki))
- Make call\_button public [\#391](https://github.com/napari/magicgui/pull/391) ([dstansby](https://github.com/dstansby))
- Add scrollable widgets [\#388](https://github.com/napari/magicgui/pull/388) ([dstansby](https://github.com/dstansby))

**Fixed bugs:**

- Return empty tuple for no selected files [\#415](https://github.com/napari/magicgui/pull/415) ([aeisenbarth](https://github.com/aeisenbarth))
- Block event emits during choices batch update [\#407](https://github.com/napari/magicgui/pull/407) ([aeisenbarth](https://github.com/aeisenbarth))
- Bug fix of type check in ListEdit [\#404](https://github.com/napari/magicgui/pull/404) ([hanjinliu](https://github.com/hanjinliu))
- Fix bug with small default range in SpinBox [\#397](https://github.com/napari/magicgui/pull/397) ([Czaki](https://github.com/Czaki))
- Fix bug in creation of RangeEdit using create\_widget [\#396](https://github.com/napari/magicgui/pull/396) ([Czaki](https://github.com/Czaki))
- Fix insertion of Container widget [\#394](https://github.com/napari/magicgui/pull/394) ([hanjinliu](https://github.com/hanjinliu))

**Tests & CI:**

- fix napari CI test [\#417](https://github.com/napari/magicgui/pull/417) ([tlambert03](https://github.com/tlambert03))
- ci\(dependabot\): bump actions/setup-python from 1 to 3 [\#414](https://github.com/napari/magicgui/pull/414) ([dependabot[bot]](https://github.com/apps/dependabot))
- ci\(dependabot\): bump codecov/codecov-action from 2 to 3 [\#413](https://github.com/napari/magicgui/pull/413) ([dependabot[bot]](https://github.com/apps/dependabot))
- ci\(dependabot\): bump actions/checkout from 2 to 3 [\#412](https://github.com/napari/magicgui/pull/412) ([dependabot[bot]](https://github.com/apps/dependabot))
- ci: add dependabot [\#411](https://github.com/napari/magicgui/pull/411) ([tlambert03](https://github.com/tlambert03))
- Fix typesafety tests [\#399](https://github.com/napari/magicgui/pull/399) ([tlambert03](https://github.com/tlambert03))

**Merged pull requests:**

- add changelog for v0.5.0 [\#418](https://github.com/napari/magicgui/pull/418) ([tlambert03](https://github.com/tlambert03))

## [v0.4.0](https://github.com/napari/magicgui/tree/v0.4.0) (2022-03-25)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.4.0rc1...v0.4.0)

**Documentation:**

- Fix pyqt conda install instruction [\#386](https://github.com/napari/magicgui/pull/386) ([dstansby](https://github.com/dstansby))

## [v0.4.0rc1](https://github.com/napari/magicgui/tree/v0.4.0rc1) (2022-03-18)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.3.7...v0.4.0rc1)

**Implemented enhancements:**

- Support sequences [\#342](https://github.com/napari/magicgui/pull/342) ([hanjinliu](https://github.com/hanjinliu))

**Fixed bugs:**

- Use empty string as null value for FileEdit [\#384](https://github.com/napari/magicgui/pull/384) ([brisvag](https://github.com/brisvag))
- fix register\_widget with widget subclass [\#376](https://github.com/napari/magicgui/pull/376) ([tlambert03](https://github.com/tlambert03))

**Deprecated:**

- Remove event deprecations strategy \(for release 0.4.0\) [\#368](https://github.com/napari/magicgui/pull/368) ([tlambert03](https://github.com/tlambert03))

**Tests & CI:**

- Check out napari repo instead of git+https [\#378](https://github.com/napari/magicgui/pull/378) ([jni](https://github.com/jni))
- Test that bound values don't get called greedily upon widget creation [\#371](https://github.com/napari/magicgui/pull/371) ([tlambert03](https://github.com/tlambert03))

## [v0.3.7](https://github.com/napari/magicgui/tree/v0.3.7) (2022-02-12)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.3.6...v0.3.7)

**Merged pull requests:**

- bump psygnal dep to 0.3.0 [\#369](https://github.com/napari/magicgui/pull/369) ([tlambert03](https://github.com/tlambert03))

## [v0.3.6](https://github.com/napari/magicgui/tree/v0.3.6) (2022-02-11)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.3.5...v0.3.6)

**Fixed bugs:**

- Fix `_normalize_slot` private attr access, and fix annotation setter forward ref resolution [\#367](https://github.com/napari/magicgui/pull/367) ([tlambert03](https://github.com/tlambert03))

## [v0.3.5](https://github.com/napari/magicgui/tree/v0.3.5) (2022-02-07)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.3.4...v0.3.5)

**Implemented enhancements:**

- Create return matcher for extensible return widget creation [\#355](https://github.com/napari/magicgui/pull/355) ([gselzer](https://github.com/gselzer))

**Fixed bugs:**

- Add new type normalization TypeWrapper, fix builtin and optional ForwardRefs [\#362](https://github.com/napari/magicgui/pull/362) ([tlambert03](https://github.com/tlambert03))
- Fix changing choices on ComboBox [\#352](https://github.com/napari/magicgui/pull/352) ([tlambert03](https://github.com/tlambert03))

**Tests & CI:**

- fix tests in xvfb-action [\#366](https://github.com/napari/magicgui/pull/366) ([tlambert03](https://github.com/tlambert03))

**Documentation:**

- update napari examples [\#357](https://github.com/napari/magicgui/pull/357) ([tlambert03](https://github.com/tlambert03))

**Merged pull requests:**

- Do not package tests [\#365](https://github.com/napari/magicgui/pull/365) ([jaimergp](https://github.com/jaimergp))
- Make Table a ValueWidget [\#360](https://github.com/napari/magicgui/pull/360) ([tlambert03](https://github.com/tlambert03))
- Update build workflow [\#344](https://github.com/napari/magicgui/pull/344) ([tlambert03](https://github.com/tlambert03))

## [v0.3.4](https://github.com/napari/magicgui/tree/v0.3.4) (2022-01-01)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.3.3...v0.3.4)

**Implemented enhancements:**

- support Qt6 [\#324](https://github.com/napari/magicgui/pull/324) ([tlambert03](https://github.com/tlambert03))
- Support partials and tz.curry [\#316](https://github.com/napari/magicgui/pull/316) ([tlambert03](https://github.com/tlambert03))

**Fixed bugs:**

- Fix buttons on PySide2 [\#343](https://github.com/napari/magicgui/pull/343) ([tlambert03](https://github.com/tlambert03))
- fix py3.10 test [\#339](https://github.com/napari/magicgui/pull/339) ([tlambert03](https://github.com/tlambert03))
- Skip bad parameter names in inject tooltip [\#336](https://github.com/napari/magicgui/pull/336) ([tlambert03](https://github.com/tlambert03))
- Relay signals from Container to Container [\#331](https://github.com/napari/magicgui/pull/331) ([hanjinliu](https://github.com/hanjinliu))
- Fix readout visibility on slider `__init__` [\#329](https://github.com/napari/magicgui/pull/329) ([tlambert03](https://github.com/tlambert03))
- Fix bug in Select widget value setter in direct API usage [\#326](https://github.com/napari/magicgui/pull/326) ([tlambert03](https://github.com/tlambert03))

**Tests & CI:**

- Pre commit ci update config [\#338](https://github.com/napari/magicgui/pull/338) ([tlambert03](https://github.com/tlambert03))
- Fixing a few test things [\#325](https://github.com/napari/magicgui/pull/325) ([tlambert03](https://github.com/tlambert03))

**Documentation:**

- adds waveform generator exemple [\#322](https://github.com/napari/magicgui/pull/322) ([glyg](https://github.com/glyg))
- add example of adding mpl FigureCanvas  to widget [\#321](https://github.com/napari/magicgui/pull/321) ([tlambert03](https://github.com/tlambert03))

## [v0.3.3](https://github.com/napari/magicgui/tree/v0.3.3) (2021-11-08)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.3.2...v0.3.3)

**Implemented enhancements:**

- Add update, asdict, and update\_widget to FunctionGui [\#309](https://github.com/napari/magicgui/pull/309) ([tlambert03](https://github.com/tlambert03))
- Add support for python 3.10 [\#294](https://github.com/napari/magicgui/pull/294) ([tlambert03](https://github.com/tlambert03))

**Fixed bugs:**

- Fix deprecation events for psygnal 0.2 [\#311](https://github.com/napari/magicgui/pull/311) ([tlambert03](https://github.com/tlambert03))

## [v0.3.2](https://github.com/napari/magicgui/tree/v0.3.2) (2021-10-22)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.3.1...v0.3.2)

**Fixed bugs:**

- Fix unbound variable in format\_number [\#303](https://github.com/napari/magicgui/pull/303) ([tlambert03](https://github.com/tlambert03))

## [v0.3.1](https://github.com/napari/magicgui/tree/v0.3.1) (2021-10-21)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.3.0...v0.3.1)

**Implemented enhancements:**

- Add stacklevel to provide better information about place of problem [\#302](https://github.com/napari/magicgui/pull/302) ([Czaki](https://github.com/Czaki))
- Table widget updates [\#301](https://github.com/napari/magicgui/pull/301) ([hanjinliu](https://github.com/hanjinliu))

## [v0.3.0](https://github.com/napari/magicgui/tree/v0.3.0) (2021-10-10)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.3.0rc2...v0.3.0)

**Implemented enhancements:**

- Return type from `register_type`, so that it can be used as a decorator [\#297](https://github.com/napari/magicgui/pull/297) ([tlambert03](https://github.com/tlambert03))

**Deprecated:**

- Remove `choices` deprecation warning from 0.2.0 [\#298](https://github.com/napari/magicgui/pull/298) ([tlambert03](https://github.com/tlambert03))

**Documentation:**

- add v0.3.0 migration guide [\#299](https://github.com/napari/magicgui/pull/299) ([tlambert03](https://github.com/tlambert03))

## [v0.3.0rc2](https://github.com/napari/magicgui/tree/v0.3.0rc2) (2021-10-10)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.3.0rc1...v0.3.0rc2)

**Fixed bugs:**

- Allow `Signal.sender()` to work regardless of importing from magicgui or Psygnal [\#296](https://github.com/napari/magicgui/pull/296) ([tlambert03](https://github.com/tlambert03))
- Catch kwargs in event emitter \(backwards compatibility with old event emitter\) [\#295](https://github.com/napari/magicgui/pull/295) ([tlambert03](https://github.com/tlambert03))

## [v0.3.0rc1](https://github.com/napari/magicgui/tree/v0.3.0rc1) (2021-10-04)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.2.11...v0.3.0rc1)

**Implemented enhancements:**

- Use psygnal instead of `EventEmitter` \(callbacks receive value directly\).  Add deprecation strategy [\#253](https://github.com/napari/magicgui/pull/253) ([tlambert03](https://github.com/tlambert03))

**Fixed bugs:**

- Replace underscore with spaces in checkbox label [\#293](https://github.com/napari/magicgui/pull/293) ([tlambert03](https://github.com/tlambert03))

**Tests & CI:**

- misc typing fixes and changlelog generator config [\#292](https://github.com/napari/magicgui/pull/292) ([tlambert03](https://github.com/tlambert03))

**Merged pull requests:**

- \[pre-commit.ci\] pre-commit autoupdate [\#291](https://github.com/napari/magicgui/pull/291) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#289](https://github.com/napari/magicgui/pull/289) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#287](https://github.com/napari/magicgui/pull/287) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))

## [v0.2.11](https://github.com/napari/magicgui/tree/v0.2.11) (2021-09-11)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.2.10...v0.2.11)

**Implemented enhancements:**

- Add close method [\#283](https://github.com/napari/magicgui/pull/283) ([tlambert03](https://github.com/tlambert03))
- Make `show_file_dialog` function public [\#274](https://github.com/napari/magicgui/pull/274) ([tlambert03](https://github.com/tlambert03))
- Add `button.clicked` alias for `button.changed` [\#271](https://github.com/napari/magicgui/pull/271) ([tlambert03](https://github.com/tlambert03))
- Add multi-Selection widget [\#265](https://github.com/napari/magicgui/pull/265) ([tlambert03](https://github.com/tlambert03))
- Add copy, paste, cut, delete keyboard shortcuts to Table widget [\#264](https://github.com/napari/magicgui/pull/264) ([tlambert03](https://github.com/tlambert03))

**Fixed bugs:**

- Fix call button text and and param options when using decorator on class method [\#276](https://github.com/napari/magicgui/pull/276) ([tlambert03](https://github.com/tlambert03))
- Fix check for Optional Type [\#270](https://github.com/napari/magicgui/pull/270) ([tlambert03](https://github.com/tlambert03))
- Change comparison to null\_value in ValueWidget from `==` to `is` [\#267](https://github.com/napari/magicgui/pull/267) ([tlambert03](https://github.com/tlambert03))
- Fix missing event emission when nullable widget is set to null value. [\#263](https://github.com/napari/magicgui/pull/263) ([tlambert03](https://github.com/tlambert03))
- Fix optional annotation affecting later widgets [\#262](https://github.com/napari/magicgui/pull/262) ([tlambert03](https://github.com/tlambert03))
- Fix RangeWidget with implicit optional type [\#257](https://github.com/napari/magicgui/pull/257) ([tlambert03](https://github.com/tlambert03))

**Tests & CI:**

- Fix typesafety tests [\#282](https://github.com/napari/magicgui/pull/282) ([tlambert03](https://github.com/tlambert03))

**Documentation:**

- Fix docs build again [\#286](https://github.com/napari/magicgui/pull/286) ([tlambert03](https://github.com/tlambert03))
- Fix docs build, add Select widget [\#285](https://github.com/napari/magicgui/pull/285) ([tlambert03](https://github.com/tlambert03))

**Merged pull requests:**

- update master to main [\#280](https://github.com/napari/magicgui/pull/280) ([tlambert03](https://github.com/tlambert03))
- \[pre-commit.ci\] pre-commit autoupdate [\#278](https://github.com/napari/magicgui/pull/278) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#272](https://github.com/napari/magicgui/pull/272) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#268](https://github.com/napari/magicgui/pull/268) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#258](https://github.com/napari/magicgui/pull/258) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#256](https://github.com/napari/magicgui/pull/256) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#254](https://github.com/napari/magicgui/pull/254) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))

## [v0.2.10](https://github.com/napari/magicgui/tree/v0.2.10) (2021-07-11)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.2.9...v0.2.10)

**Implemented enhancements:**

- Add `tracking` property to sliders.  When False, changed only emits on release. [\#248](https://github.com/napari/magicgui/pull/248) ([tlambert03](https://github.com/tlambert03))
- Add ValueWidget.\_nullable, and enable for categorical widgets [\#227](https://github.com/napari/magicgui/pull/227) ([tlambert03](https://github.com/tlambert03))

**Fixed bugs:**

- Fix labels remaining after popping widgets from container [\#245](https://github.com/napari/magicgui/pull/245) ([tlambert03](https://github.com/tlambert03))
- Fix default value of None being ignored [\#244](https://github.com/napari/magicgui/pull/244) ([tlambert03](https://github.com/tlambert03))
- Fix reuse of magic factory [\#224](https://github.com/napari/magicgui/pull/224) ([tlambert03](https://github.com/tlambert03))
- Fix EventEmitter loop when event is blocked [\#215](https://github.com/napari/magicgui/pull/215) ([tlambert03](https://github.com/tlambert03))

**Documentation:**

- Small change to improve repr of sentinel in docs [\#251](https://github.com/napari/magicgui/pull/251) ([tlambert03](https://github.com/tlambert03))
- Minor docstring change for tracking [\#250](https://github.com/napari/magicgui/pull/250) ([tlambert03](https://github.com/tlambert03))
- Specify XDG\_RUNTIME\_DIR to avoid warnings showing up in the docs [\#249](https://github.com/napari/magicgui/pull/249) ([hmaarrfk](https://github.com/hmaarrfk))
- Fix FunctionGui docstring parameter name [\#247](https://github.com/napari/magicgui/pull/247) ([tlambert03](https://github.com/tlambert03))
- fix-docs [\#231](https://github.com/napari/magicgui/pull/231) ([tlambert03](https://github.com/tlambert03))
- Widget overview docs [\#213](https://github.com/napari/magicgui/pull/213) ([tlambert03](https://github.com/tlambert03))

**Merged pull requests:**

- \[pre-commit.ci\] pre-commit autoupdate [\#235](https://github.com/napari/magicgui/pull/235) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#228](https://github.com/napari/magicgui/pull/228) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#223](https://github.com/napari/magicgui/pull/223) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#221](https://github.com/napari/magicgui/pull/221) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#219](https://github.com/napari/magicgui/pull/219) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))

## [v0.2.9](https://github.com/napari/magicgui/tree/v0.2.9) (2021-04-05)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.2.8...v0.2.9)

**Implemented enhancements:**

- Display current slider value \(editable\) [\#211](https://github.com/napari/magicgui/pull/211) ([tlambert03](https://github.com/tlambert03))
- Add table.changed event emitter [\#209](https://github.com/napari/magicgui/pull/209) ([tlambert03](https://github.com/tlambert03))
- Coerce RadioButton with Enum/choices to RadioButtons [\#202](https://github.com/napari/magicgui/pull/202) ([tlambert03](https://github.com/tlambert03))
- Compute correct widget width for rich text labels [\#199](https://github.com/napari/magicgui/pull/199) ([maweigert](https://github.com/maweigert))

**Fixed bugs:**

- Fix tests when both pyside2 and pyqt5 are installed [\#210](https://github.com/napari/magicgui/pull/210) ([tlambert03](https://github.com/tlambert03))
- Disconnect filedialog button from value.changed events [\#208](https://github.com/napari/magicgui/pull/208) ([tlambert03](https://github.com/tlambert03))
- Fix persist issue with cached parameter that has been removed [\#203](https://github.com/napari/magicgui/pull/203) ([uschmidt83](https://github.com/uschmidt83))
- fix enum choices in radiobuttons [\#201](https://github.com/napari/magicgui/pull/201) ([tlambert03](https://github.com/tlambert03))
- Delete button when removing from qt RadioGroup [\#198](https://github.com/napari/magicgui/pull/198) ([tlambert03](https://github.com/tlambert03))

**Documentation:**

- skip docutils 0.17 [\#207](https://github.com/napari/magicgui/pull/207) ([tlambert03](https://github.com/tlambert03))
- Add cache location hint to persist option documentation [\#200](https://github.com/napari/magicgui/pull/200) ([maweigert](https://github.com/maweigert))

**Merged pull requests:**

- \[pre-commit.ci\] pre-commit autoupdate [\#212](https://github.com/napari/magicgui/pull/212) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))

## [v0.2.8](https://github.com/napari/magicgui/tree/v0.2.8) (2021-03-24)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.2.8rc0...v0.2.8)

## [v0.2.8rc0](https://github.com/napari/magicgui/tree/v0.2.8rc0) (2021-03-24)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.2.7...v0.2.8rc0)

**Implemented enhancements:**

- Update call button to default True when auto\_call is False [\#194](https://github.com/napari/magicgui/pull/194) ([jni](https://github.com/jni))
- add `RadioButtons` widget [\#183](https://github.com/napari/magicgui/pull/183) ([tlambert03](https://github.com/tlambert03))

**Fixed bugs:**

- Fix RadioButtons double event emissions [\#189](https://github.com/napari/magicgui/pull/189) ([tlambert03](https://github.com/tlambert03))
- don't ever change the call\_button text silly [\#180](https://github.com/napari/magicgui/pull/180) ([tlambert03](https://github.com/tlambert03))
- Fix extreme float values for slider and spinbox [\#178](https://github.com/napari/magicgui/pull/178) ([tlambert03](https://github.com/tlambert03))
- Fix FileEdit events [\#176](https://github.com/napari/magicgui/pull/176) ([tlambert03](https://github.com/tlambert03))
- fix nested functiongui show [\#175](https://github.com/napari/magicgui/pull/175) ([tlambert03](https://github.com/tlambert03))
- Fail gracefully with persistence errors, better debounce [\#170](https://github.com/napari/magicgui/pull/170) ([tlambert03](https://github.com/tlambert03))

**Documentation:**

- docs reorg [\#193](https://github.com/napari/magicgui/pull/193) ([tlambert03](https://github.com/tlambert03))

**Merged pull requests:**

- Replace turbo with magma colormap in tests [\#195](https://github.com/napari/magicgui/pull/195) ([jni](https://github.com/jni))
- \[pre-commit.ci\] pre-commit autoupdate [\#191](https://github.com/napari/magicgui/pull/191) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- fix mypy errors [\#185](https://github.com/napari/magicgui/pull/185) ([tlambert03](https://github.com/tlambert03))
- \[pre-commit.ci\] pre-commit autoupdate [\#184](https://github.com/napari/magicgui/pull/184) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Add typing to events.py [\#181](https://github.com/napari/magicgui/pull/181) ([tlambert03](https://github.com/tlambert03))
- \[pre-commit.ci\] pre-commit autoupdate [\#171](https://github.com/napari/magicgui/pull/171) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))

## [v0.2.7](https://github.com/napari/magicgui/tree/v0.2.7) (2021-02-28)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.2.6rc0...v0.2.7)

**Implemented enhancements:**

- improve error message for bad kwargs [\#167](https://github.com/napari/magicgui/pull/167) ([tlambert03](https://github.com/tlambert03))
- Persist parameter values across sessions [\#160](https://github.com/napari/magicgui/pull/160) ([tlambert03](https://github.com/tlambert03))
- Add `widget_init` parameter to `magic_factory` [\#159](https://github.com/napari/magicgui/pull/159) ([tlambert03](https://github.com/tlambert03))
- Allow `magicgui.types.PathLike` annotation [\#151](https://github.com/napari/magicgui/pull/151) ([tlambert03](https://github.com/tlambert03))
- allow label to be alias for text in button widgets [\#150](https://github.com/napari/magicgui/pull/150) ([tlambert03](https://github.com/tlambert03))
- Image widget [\#140](https://github.com/napari/magicgui/pull/140) ([tlambert03](https://github.com/tlambert03))

**Fixed bugs:**

- fix range/slice edits [\#166](https://github.com/napari/magicgui/pull/166) ([tlambert03](https://github.com/tlambert03))
- Work without numpy [\#164](https://github.com/napari/magicgui/pull/164) ([tlambert03](https://github.com/tlambert03))
- Fix FileEdit with directory mode [\#158](https://github.com/napari/magicgui/pull/158) ([tlambert03](https://github.com/tlambert03))
- fix function with no params and callbutton [\#149](https://github.com/napari/magicgui/pull/149) ([tlambert03](https://github.com/tlambert03))
- Fix typesafety checks with numpy 1.20 [\#141](https://github.com/napari/magicgui/pull/141) ([tlambert03](https://github.com/tlambert03))
- Disable call button while function is running [\#139](https://github.com/napari/magicgui/pull/139) ([tlambert03](https://github.com/tlambert03))

**Documentation:**

- Fix napari return annotations [\#154](https://github.com/napari/magicgui/pull/154) ([sofroniewn](https://github.com/sofroniewn))

**Merged pull requests:**

- \[pre-commit.ci\] pre-commit autoupdate [\#157](https://github.com/napari/magicgui/pull/157) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#148](https://github.com/napari/magicgui/pull/148) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Move return\_annotation from container to FunctionGui [\#143](https://github.com/napari/magicgui/pull/143) ([tlambert03](https://github.com/tlambert03))
- \[pre-commit.ci\] pre-commit autoupdate [\#142](https://github.com/napari/magicgui/pull/142) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Remove pre 0.2.0 deprecation warnings [\#138](https://github.com/napari/magicgui/pull/138) ([tlambert03](https://github.com/tlambert03))
- update changelog [\#137](https://github.com/napari/magicgui/pull/137) ([tlambert03](https://github.com/tlambert03))
- \[pre-commit.ci\] pre-commit autoupdate [\#136](https://github.com/napari/magicgui/pull/136) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))

## [v0.2.6rc0](https://github.com/napari/magicgui/tree/v0.2.6rc0) (2021-01-25)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.2.6...v0.2.6rc0)

## [v0.2.6](https://github.com/napari/magicgui/tree/v0.2.6) (2021-01-25)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.2.5...v0.2.6)

**Merged pull requests:**

- Add `magicgui.*` objectName to qt widgets [\#134](https://github.com/napari/magicgui/pull/134) ([tlambert03](https://github.com/tlambert03))
- remove \_qt module [\#133](https://github.com/napari/magicgui/pull/133) ([tlambert03](https://github.com/tlambert03))
- Improve fallback behavior of tqdm iterator inside of \*hidden\* magicgui widget [\#131](https://github.com/napari/magicgui/pull/131) ([tlambert03](https://github.com/tlambert03))
- Improve issues with widget visibility [\#130](https://github.com/napari/magicgui/pull/130) ([tlambert03](https://github.com/tlambert03))
- add attribute error to `magicgui.__getattr__` [\#129](https://github.com/napari/magicgui/pull/129) ([tlambert03](https://github.com/tlambert03))
- Make `_magicgui.pyi` stubs [\#126](https://github.com/napari/magicgui/pull/126) ([tlambert03](https://github.com/tlambert03))
- Fix `@magic_factory` usage in local scopes [\#125](https://github.com/napari/magicgui/pull/125) ([tlambert03](https://github.com/tlambert03))
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

**Merged pull requests:**

- Fix reset\_choices recursion [\#96](https://github.com/napari/magicgui/pull/96) ([tlambert03](https://github.com/tlambert03))
- better bound values [\#95](https://github.com/napari/magicgui/pull/95) ([tlambert03](https://github.com/tlambert03))

## [v0.2.4](https://github.com/napari/magicgui/tree/v0.2.4) (2021-01-12)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.2.3...v0.2.4)

**Merged pull requests:**

- Extend combobox api with set\_choice, get\_choice, del\_choice [\#92](https://github.com/napari/magicgui/pull/92) ([tlambert03](https://github.com/tlambert03))

## [v0.2.3](https://github.com/napari/magicgui/tree/v0.2.3) (2021-01-08)

[Full Changelog](https://github.com/napari/magicgui/compare/v0.2.2...v0.2.3)

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
