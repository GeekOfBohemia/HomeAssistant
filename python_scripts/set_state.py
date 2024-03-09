#==================================================================================================
#  python_scripts/set_state.py 
#==================================================================================================

#--------------------------------------------------------------------------------------------------
# Set the state or other attributes for the entity specified in the Automation Action
# Priklad: 
# -----------------------------------
# service: python_script.set_state
# data_template:
#  entity_id: binary_sensor.honeywell_ok
#  state: "off"
# -----------------------------------
#--------------------------------------------------------------------------------------------------

inputEntity = data.get('entity_id')
if inputEntity is None:
    logger.warning("===== entity_id je povinne pole.")
else:    
    inputStateObject = hass.states.get(inputEntity)
    inputState = inputStateObject.state
    inputAttributesObject = inputStateObject.attributes.copy()

    for item in data:
        newAttribute = data.get(item)
        logger.debug(f"===== item = {item}; value = {newAttribute}")
        if item == 'entity_id':
            continue            # already handled
        elif item == 'state':
            inputState = newAttribute
        else:
            inputAttributesObject[item] = newAttribute
        
    hass.states.set(inputEntity, inputState, inputAttributesObject)
