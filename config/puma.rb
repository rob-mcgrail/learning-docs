workers Integer(ENV['PUMA_WORKERS'] || 3)
threads Integer(ENV['MIN_THREADS']  || 2), Integer(ENV['MAX_THREADS'] || 4)

preload_app!

rackup      DefaultRackup
bind        ENV['BIND'] || 'tcp://0.0.0.0:3000'
environment ENV['ENVIRONMENT'] || 'development'

# on_worker_boot do
#   # worker specific setup
#   ActiveSupport.on_load(:active_record) do
#     config = ActiveRecord::Base.configurations[Rails.env] ||
#                 Rails.application.config.database_configuration[Rails.env]
#     config['pool'] = ENV['MAX_THREADS'] || 16
#     ActiveRecord::Base.establish_connection(config)
#   end
# end
