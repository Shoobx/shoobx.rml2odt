CHANGES
=======

0.9.0 (2025-02-27)
------------------

- Moving CI to github actions

- Python 3.9, 3.10, 3.11 compatibility


0.8.0 (2020-12-08)
------------------

- Upgrade to py3.7+

- Changes for z3c.rml 4+ dependency


0.7.1 (2020-02-26)
------------------

- Add support for nested lists with different styling than parent


0.7.0 (2019-08-19)
------------------

- Add minor support for `keepTogether` tags, always displaying contents and
  keeping direct child `blockTable` elements on the same page


0.6.1 (2019-08-16)
------------------

- Add support for `spanStyle` tags.

- Add support for `underline` attribute is `paraStyle` and `spanStyle` tags.


0.6.0 (2019-04-12)
------------------

- Complete overhaul of blockTable styling.
  This enables the use blockTableStyle and `td` styling tags.
  Most text, background and border styling is supported.


0.5.0 (2019-04-05)
------------------

- Fix: `img` must be in a Paragraph otherwise LibreOffice will not show the
  Image

- Code cleanup and refactor

- Lots of fixes, cleanup, tests added

- Fix: blockSpan handling was completely broken

- Fix: Removed whitespace from `para` left text,
  removed tail text of `para` tag

- Fix: `NextPage` did not work, it added no page break

- Fix: Do not add tabs to the ODT output, reportlab does not either.
  There's a special `tab` tag that is used by our custom numbering.

- Fix: Do not fail on missing `value` of the `color` tag

- Fix: Support `pre` and `xpre` tags, make sure whitespace is not squashed

- Fix: Copy the `main` or `Main` pageTemplate to `Standard` to make ODT
  at least somehow happy. Reportlab uses `main` as conventional default.
  This is still just a workaround. Supporting custom templates set in a story
  will take more efforts.

- Copied all z3c.rml RML test inputs, blacklisted a lot, listed shortcomings.

0.4.4 (2019-03-26)
------------------

- Fix: Next paragraph text strip for custom bullets broken by 0.4.3.


0.4.3 (2019-03-26)
------------------

- Fix: bullet numbering ignored `value` as start

- Fix: support all custom `li` bullets (l, L, o, O, r, R)


0.4.2 (2019-03-20)
------------------

- Fix: the `br` tag used a class variable to remember whether it added the
  style `BreakJustify`.
- Fix `span` tag handling. It literally discarded most text.


0.4.1 (2019-03-19)
------------------

- Fix: Text following a comment tag was discarded.

- Fix: 3+ whitespace was replaced with nothing. Caused text to miss spaces.


0.4.0 (2018-01-23)
------------------

- More indentation fixes.

- Added support for O format lists (First, Second, Third)

- Add support to have bullet lists in number lists and vice versa

- Convert tables in lists to lists in lists

- Support for blockSpan in table styles.

- Handle tail text of comments

- Supporting RML blockSpan styles for tables

- Take the maximum, not the first when calculating the number of columns


0.3.0 (2018-01-12)
------------------

- Many many formatting fixes including an almost complete rewrite of
  list handling and list styles.


0.2.0 (2017-12-08)
------------------

- Cleaned up the public API.

- Added basic docs.


0.1.0 (2017-11-21)
------------------

- Basic Support for:

  * Flowables: para, blockTable, hr, ul, ol

  * Stylesheets: paraStyle

  * Page Layout

- Initial Release
