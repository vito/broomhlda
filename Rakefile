task :clean do
  sh "find . -name '*.rbc' -delete; find . -name '*.ayc' -delete"
end

task :install do
  sh "rm *.gem; gem uninstall broomhlda -x; gem build broomhlda.gemspec && gem install broomhlda*.gem --local --no-ri --no-rdoc"
end
