Gem::Specification.new do |s|
  s.name     = "broomhlda"
  s.version  = "0.0.1"
  s.authors  = ["Alex Suraci"]
  s.email    = ["suraci.alex@gmail.com"]
  s.homepage = "http://atomy-lang.org"
  s.summary  = "broomhlda syntax highlighter and tokenizer"

  s.files         = %w{LICENSE.md} + Dir["lib/**/*"]
  s.require_paths = ["lib"]

  s.license = "Apache-2.0"

  s.has_rdoc = false

  s.add_runtime_dependency "atomy", "~> 0.4"

  s.add_development_dependency "rake"
end
