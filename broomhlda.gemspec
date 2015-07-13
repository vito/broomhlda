Gem::Specification.new do |s|
  s.name     = "broomhlda"
  s.version  = "0.2.2"
  s.authors  = ["Alex Suraci"]
  s.email    = ["suraci.alex@gmail.com"]
  s.homepage = "https://vito.github.io/atomy"
  s.summary  = "broomhlda syntax highlighter and tokenizer"

  s.description = %q{
    A DSL for authoring lexers, largely based on Pygments (with many of its
    lexers auto-converted).
  }

  s.files         = %w{LICENSE.md} + Dir["lib/**/*"]
  s.require_paths = ["lib"]

  s.license = "Apache-2.0"

  s.has_rdoc = false

  s.add_runtime_dependency "atomy", "~> 0.6.3"

  s.add_development_dependency "rake", "~> 10.4"
end
