import forallpeople as si

# By initializing the environment in this central module, we ensure it's done
# only once. Other modules can then import the configured 'si' object.
si.environment('test_definitions', top_level=False)