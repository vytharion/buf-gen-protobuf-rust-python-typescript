//! Prost + tonic bindings for the `monorepo.v1` schemas.
//!
//! The contents of `src/gen/` are produced by `buf generate` (see
//! `buf.gen.yaml` at the repository root). Rerun the generator after
//! editing any `.proto` file in `proto/monorepo/v1/`.

#![forbid(unsafe_code)]
#![deny(rust_2018_idioms)]

pub mod gen;

pub use gen::monorepo;
pub use gen::monorepo::v1;

/// Encoded `FileDescriptorSet` for the `monorepo.v1` package, emitted
/// by the `file_descriptor_set` opt on the prost plugin. Useful for
/// reflection servers (`tonic-reflection`) and CLI tooling that needs
/// to introspect the schema at runtime.
pub const FILE_DESCRIPTOR_SET: &[u8] = gen::FILE_DESCRIPTOR_SET;

/// Returns the proto package name that every generated symbol lives
/// under. Pinning it as a `const` keeps tests honest if the namespace
/// ever drifts during a schema migration.
pub const PROTO_PACKAGE: &str = "monorepo.v1";
