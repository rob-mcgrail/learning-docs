class Competency < ActiveRecord::Base
  has_and_belongs_to_many :skills
  has_many :tasks, through: :skills

  validates :title, presence: true, length: { maximum: 128 }

  include RendersMarkdown
  renders_markdown :description

  include RelaysCollectionCompleteness
  relays_completeness_for_collections :skills, :tasks

  include IsSubscribable
  subscription_type_name 'Competency'
end
