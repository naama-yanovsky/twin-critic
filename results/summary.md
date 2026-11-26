| Scenario | Mode | Attempts | End state | Expected | Matches |
| --- | --- | --- | --- | --- | --- |
| 1-existing-info | language model | 1 | approved | approved | yes |
| 2a-follow-up-first | language model | 1 | approved | approved | yes |
| 2b-follow-up-second | language model | 1 | approved | approved | yes |
| 3-missing-info | language model | 1 | approved | approved | yes |
| 4-reject-and-improve | language model | 2 | approved | approved | yes |
| 5-attempts-exhausted [MOCK] | mock | 3 | attempts_exhausted | attempts_exhausted | yes |
| extra-technical-error [MOCK] | mock | 1 | technical_error | technical_error | yes |
