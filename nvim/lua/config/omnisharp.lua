return {
  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        omnisharp = {
          enable_roslyn_analyzers = true,
          enable_import_completion = true,
          organize_imports_on_format = true,
          settings = {
            RoslynExtensionsOptions = {
              enableDecompilationSupport = true,
              enableAnalyzersSupport = true,
            },
          },
        },
      },
    },
  },
}
