//! Module tree for `buf generate` output.
//!
//! Every sibling `.rs` file in this directory is overwritten on every
//! regeneration. The hand-written entries in this file wire those
//! generated files into the crate's module hierarchy so consumers can
//! reach the prost message structs and tonic service stubs through
//! ergonomic Rust paths (`monorepo_pb::v1::Money`, etc).

#![allow(clippy::all)]
#![allow(rustdoc::broken_intra_doc_links)]

pub mod monorepo {
    pub mod v1 {
        include!("monorepo.v1.rs");
        include!("monorepo.v1.tonic.rs");
    }
}

pub(crate) const FILE_DESCRIPTOR_SET: &[u8] =
    include_bytes!("file_descriptor_set.bin");
