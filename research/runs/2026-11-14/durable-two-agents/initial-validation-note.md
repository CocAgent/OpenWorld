# Initial validation findings

The first targeted run contained 13 tests. Twelve passed; the restart-history
comparison failed because the live Python records contained tuples whereas the
CLI returned JSON lists. The world fingerprint, budget and memory comparisons
matched. Normalizing round records to JSON data types resolved the failure.
A further atomic cross-agent projection test brings the final targeted count
to 14.

The first full validation at source
`ef369403230909241172a5885d7cb544ada2e151` executed all checks successfully.
Its [raw full-suite log](initial-full-tests.log) records 500 tests in 134.994
seconds, six skips and two expected failures. The wrapper subsequently exited
with an error while printing the accented output-directory path to a Windows
cp1252 console:

```text
UnicodeEncodeError: 'charmap' codec can't encode character '\u0300' in position 69: character maps to <undefined>
```

The completion message was changed to ASCII in `c0dae57`. The final
`validation.json` and its listed logs come from a subsequent complete invocation
at that source, with real commands and exit codes. The initial failure is not
presented as a successful wrapper invocation. No runtime or test logic changed
for the console fix.
