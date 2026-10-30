<!-- SPDX-License-Identifier: Apache-2.0 -->

# Container — Model Import and Connection

**Status:** target specification. The current model registry stores metadata only; it does not fetch or inspect model contents. See [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md).

## 1. One entry point

The user should be able to say "use this model", paste a URL, drop a ZIP, select local files, or provide an inference endpoint in the main conversation. Container identifies the source type and guides the user through the relevant path.

A URL is not one universal operation. A repository URL means inspect/import files; a hosted inference URL means connect to a service; a local runtime URL means register a reachable user-owned endpoint. The UI must identify this difference instead of downloading every URL.

## 2. Supported source classes

The import system is adapter-based. "Supported" means an inspected adapter exists and has tests; it does not mean every URL or every model architecture is guaranteed to work.

| Source class | Expected behavior |
|---|---|
| Model repository URL | Read repository metadata and supported file manifests; select a revision; inspect license, configuration, tokenizer, weights, adapters, and related files; import selected artifacts. |
| Direct HTTPS file URL | Fetch an explicitly supported model/config/tokenizer file after destination, type, size, and integrity checks. |
| ZIP archive upload | Inspect the archive manifest first; identify supported model packages; show contents and total expanded size; safely extract approved files. |
| Local file or folder | Upload selected files or a packaged directory; preserve relative manifest structure without trusting user filenames as storage keys. |
| Hosted inference endpoint | Register connection metadata, API format/capabilities, auth reference, health, and limits; do not download weights. |
| Local model-server endpoint | Register a user-owned runtime endpoint when it is securely reachable through an approved connector/desktop bridge. |
| Provider/model catalog entry | Connect through a provider adapter and retain provider/model identity, terms, capabilities, and usage metadata. |
| Container artifact | Reuse an already uploaded, authorized artifact within the same permitted facility/project scope. |

Potential model artifact formats include formats such as Safetensors, GGUF, ONNX, and compatible framework checkpoints, plus tokenizer/configuration and adapter files. A format is importable only when the corresponding parser, runtime, and security checks are implemented. Container must not promise universal model compatibility.

## 3. User experience

1. **Receive:** user pastes a URL or uploads files in chat.
2. **Classify:** determine repository, direct file, archive, local upload, hosted endpoint, or local runtime endpoint.
3. **Inspect:** retrieve limited metadata and a manifest without executing imported code.
4. **Explain:** show model/repository identity, revision, source, formats, license/terms, approximate size, detected architecture, and unknown fields.
5. **Check:** validate compatibility against available runtimes and compute profiles.
6. **Estimate:** estimate download/storage and, when relevant, inference/training resource requirements and cost.
7. **Confirm:** obtain consent before chargeable downloads/compute, provider calls, or consequential access.
8. **Import or connect:** copy verified artifacts to private storage or register the endpoint securely.
9. **Validate:** verify hashes and required file relationships; run a safe metadata/runtime check or a constrained test request.
10. **Register:** create an immutable model version and provenance record.
11. **Continue:** offer contextual next actions such as test chat, compare, evaluate, adapt, or deploy, only when supported.

The Core panel and conversation should display import progress, warnings, and a clear final state. Failed or partial imports must be resumable or safely cleaned up.

## 4. Repository import details

A repository adapter should record:
- Canonical repository URL and provider.
- Repository owner/name when available.
- Exact commit/revision or immutable snapshot identifier.
- File manifest, selected files, sizes, and checksums.
- Model architecture/configuration metadata.
- Tokenizer and vocabulary references.
- License identifier and source terms, including uncertainty.
- Model card/readme reference and retrieval timestamp.
- Importer version and any warnings.

The importer should support selecting a subset of large files when possible. It must not assume that the default branch is immutable or that a model card's license string fully establishes redistribution rights.

## 5. Archive and file handling

ZIP handling must defend against:
- Path traversal and absolute paths.
- Symlinks and hard-link surprises.
- Duplicate or ambiguous filenames.
- Zip bombs and excessive expanded size/file counts.
- Decompression time and memory exhaustion.
- Malformed or nested archives.
- Unexpected executables, scripts, or custom code.

Use generated storage keys, normalized manifests, size and count limits, content sniffing, checksums, and isolated extraction. Never execute scripts or custom model code simply because they appear in an archive. Do not load pickle-based checkpoints in a privileged API process. Formats with executable/custom-code risks require an isolated, explicit opt-in path and additional review.

## 6. URL and network security

All URL fetchers require SSRF protections:
- Permit only explicitly supported schemes, normally HTTPS for public repository/file sources.
- Reject loopback, private, link-local, multicast, reserved, and cloud metadata destinations unless a separately authorized local connector is in use.
- Resolve and validate DNS at connection time; defend against rebinding and redirects to prohibited addresses.
- Revalidate every redirect and enforce host/port policy.
- Apply connection/read timeouts, maximum response size, redirect count, concurrency, and per-user rate limits.
- Do not forward ambient credentials or internal headers to remote origins.
- Keep endpoint credentials in secret storage, not in URLs, logs, events, or conversation history.

Local model-server endpoints are a separate trust boundary. They should be reachable only through explicit opt-in, a paired local connector, or a safe private network configuration—not by weakening public URL protections.

## 7. Compatibility contract

Compatibility inspection should consider:
- Architecture and model family.
- Weight format and sharding/index files.
- Tokenizer/configuration completeness.
- Quantization and numerical format.
- Runtime/engine support and version.
- Required CPU instruction sets, GPU type, accelerator memory, RAM, and disk.
- Context length, modality, and required auxiliary assets.
- License and permitted intended use.

Return a clear status: supported, supported with limitations, unsupported, or needs manual review. Never silently substitute a different model or incompatible runtime.

## 8. Registry lifecycle

A model identity groups related versions. Each version records source, revision, artifact hashes, imported files, license/provenance, architecture/format, import status, compatibility results, runtime tests, and optional training/evaluation lineage.

Connected endpoints are registered as endpoint/provider resources, not falsely represented as locally stored weight files. Credentials are stored separately and are never returned in API responses.

## 9. Non-goals and honesty

- A model URL is not proof that the model is safe, licensed for every use, or compatible.
- A successful metadata import is not proof that inference works.
- A connected endpoint is not a downloaded model.
- A registered model is not automatically trained, evaluated, or deployed.
- A format name alone is not enough to certify compatibility.

All user-visible support claims must be generated from the actual installed adapters and runtime capability registry.
