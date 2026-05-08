content = open('main.py', 'r', encoding='utf-8').read()

# Fix reservation flow save calls to preserve session_data
old_step1 = """if current_step == 1:  # Fecha
                                # Guardar fecha seleccionada
                                database.save_user_session(numero_usuario, phone_number_id, {
                                    'reservation_flow': {
                                        'step': 2,
                                        'fecha': texto_usuario,
                                        'inicio': flow_state.get('inicio')
                                    }
                                })"""

new_step1 = """if current_step == 1:  # Fecha
                                # Guardar fecha seleccionada - preservar session_data
                                from copy import deepcopy
                                new_session_data = deepcopy(session.get('session_data', {}))
                                new_session_data['reservation_flow'] = {
                                    'step': 2,
                                    'fecha': texto_usuario,
                                    'inicio': flow_state.get('inicio')
                                }
                                database.save_user_session(numero_usuario, phone_number_id, new_session_data)"""

content = content.replace(old_step1, new_step1)

old_step2 = """elif current_step == 2:  # Personas
                                # Guardar numero de personas
                                database.save_user_session(numero_usuario, phone_number_id, {
                                    'reservation_flow': {
                                        'step': 3,
                                        'fecha': flow_state.get('fecha'),
                                        'personas': texto_usuario,
                                        'inicio': flow_state.get('inicio')
                                    }
                                })"""

new_step2 = """elif current_step == 2:  # Personas
                                # Guardar numero de personas - preservar session_data
                                from copy import deepcopy
                                new_session_data = deepcopy(session.get('session_data', {}))
                                new_session_data['reservation_flow'] = {
                                    'step': 3,
                                    'fecha': flow_state.get('fecha'),
                                    'personas': texto_usuario,
                                    'inicio': flow_state.get('inicio')
                                }
                                database.save_user_session(numero_usuario, phone_number_id, new_session_data)"""

content = content.replace(old_step2, new_step2)

old_step3 = """elif current_step == 3:  # Horario
                                # Guardar horario
                                database.save_user_session(numero_usuario, phone_number_id, {
                                    'reservation_flow': {
                                        'step': 4,
                                        'fecha': flow_state.get('fecha'),
                                        'personas': flow_state.get('personas'),
                                        'horario': texto_usuario,
                                        'inicio': flow_state.get('inicio')
                                    }
                                })"""

new_step3 = """elif current_step == 3:  # Horario
                                # Guardar horario - preservar session_data
                                from copy import deepcopy
                                new_session_data = deepcopy(session.get('session_data', {}))
                                new_session_data['reservation_flow'] = {
                                    'step': 4,
                                    'fecha': flow_state.get('fecha'),
                                    'personas': flow_state.get('personas'),
                                    'horario': texto_usuario,
                                    'inicio': flow_state.get('inicio')
                                }
                                database.save_user_session(numero_usuario, phone_number_id, new_session_data)"""

content = content.replace(old_step3, new_step3)

old_step4 = """# Limpiar sesion de reserva
                                database.delete_user_session(numero_usuario, phone_number_id)"""

new_step4 = """# Limpiar solo reservation_flow, mantener demo
                                from copy import deepcopy
                                new_session_data = deepcopy(session.get('session_data', {}))
                                if 'reservation_flow' in new_session_data:
                                    del new_session_data['reservation_flow']
                                database.save_user_session(numero_usuario, phone_number_id, new_session_data)"""

content = content.replace(old_step4, new_step4)

open('main.py', 'w', encoding='utf-8').write(content)
print('Fixed all reservation flow save calls')
