# unit

Fast tests that run without Postgres, S3 or the network. `uv run pytest` runs them on any machine.

| File | Covers |
| --- | --- |
| `test_images.py` | Photo rules: formats, long edge, ratio, EXIF rotation, forged headers, fuzzed damaged files |
| `test_request_hash.py` | Submission fingerprint: equal for the same instant in any offset, different for any changed field |
| `test_meal_response.py` | Response `media` exposes only public variants, keyed by kind |
| `test_body_limit.py` | Request size middleware: pass, 413 with connection close, 411 for chunked bodies |
| `test_config.py` | Token minimum length, and that the token never appears in errors or `repr` |
| `test_storage.py` | S3 adapter: bucket creation only on 404, and which failures count as unavailable |

## Trade-offs

- **S3 behaviour is tested with botocore's `Stubber`**, which checks requests and canned responses without a server. It cannot catch differences between SeaweedFS and S3 themselves; the full-stack check in the [getting started](../../../doc/developer/backend/getting-started.md) guide covers that.
- **The fuzz test uses a fixed seed and 200 samples**, so it is repeatable and fast rather than exhaustive.
