# module DeviseHelper
#   # Define a method which signs in as a valid user.
#   def sign_in_as_a_valid_user
#     # Ask factory girl to generate a valid user for us.
#     @user ||= FactoryGirl.create :user

#     # We action the login request using the parameters before we begin.
#     # The login requests will match these to the user we just created in the factory, and authenticate us.
#     post user_session_path, 'user[email]' => @user.email, 'user[password]' => @user.password
#   end
# end

# RSpec.configure do |config|
#   # Include the help for the request specs.
#   config.include DeviseHelper
# end
