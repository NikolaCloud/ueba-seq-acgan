# Rule-guided pseudo-anomaly profiles

The normal-only Seq-GAN never sees an observed CERT anomaly while training.  Its
discriminator receives only normal sequences, their reconstruction, and a
synthetic *pseudo-anomaly* made by applying one of the profiles below to normal
behaviour in the transformed feature space.  These profiles provide a useful
training signal; they are not claimed to be real attacks or GAN-generated ground
truth.

| Profile | Knowledge basis | Perturbed CERT daily features |
| --- | --- | --- |
| `usb_exfiltration` | ATT&CK T1052.001 | `device_connect`, file activity/content, after-hours activity |
| `valid_account_after_hours` | ATT&CK T1078 | logon count/events and after-hours activity |
| `web_exfiltration` | ATT&CK T1041 | HTTP activity, job-search HTTP indicator, after-hours activity |
| `external_email_collection` | ATT&CK T1114 | mail volume, external mail, size and attachments |
| `data_staging` | ATT&CK T1074 | file activity/content and device activity |
| `compound_insider_deviation` | UEBA/BDU-oriented local profile | after-hours, USB, file and external-mail deviation |

Each training sample selects one profile at random and raises only the listed
features at the most recent point in the behaviour sequence. This makes the
mapping auditable and prevents unavailable telemetry from being invented.  The
profiles must be reviewed and tuned to the organisation's own threat model,
telemetry definitions, and BDU FSTEC catalogue mapping before production use.

Observed CERT anomaly labels remain isolated for validation and final test
metrics (PR-AUC, precision and recall); they are not used to choose normal
training samples or pseudo-anomaly labels.
