??    ?        ?   ?	      8  -  9    g  M   ?  b   ?  _   7  ?  ?  J   (  F   i(  '   ?(     ?(     ?(     ?(  
   ?(     ?(     )     )     %)  %   8)     ^)     l)     ~)     ?)     ?)     ?)     ?)     ?)     ?)     *     *     (*     6*  
   D*     O*     ^*     m*  
   ?*     ?*     ?*     ?*  	   ?*     ?*     ?*  W   ?*     =+  	   D+     N+      c+     ?+     ?+     ?+  	   ?+     ?+     ?+      ?+     ?+     ?+     ,     ,     *,     2,     N,  
   _,  
   j,  	   u,     ,  
   ?,     ?,  6   ?,     ?,     ?,  &   
-     1-     @-     P-     U-     h-     }-     ?-     ?-     ?-     ?-     ?-     ?-     ?-     ?-  '   ?-     .     .     $.     4.     B.     R.     _.     l.     y.  	   ?.     ?.     ?.  %   ?.     ?.     ?.     ?.     ?.     /     /     /     5/     </     L/     _/     w/     ?/     ?/     ?/     ?/     ?/     ?/     ?/     ?/     0  +   0  0   H0  .   y0     ?0     ?0  	   ?0     ?0  	   ?0     ?0     ?0     1     1     11  	   F1     P1     \1     e1     1     ?1     ?1     ?1     ?1  
   ?1     ?1     ?1     ?1     ?1     2     2     -2     >2  	   C2     M2     f2     l2     q2    ?2  6  ?3  '  ?6  U    :  o   V:  o   ?:  ?  6;  J   ?N  K   ,O  !   xO     ?O     ?O     ?O     ?O  	   ?O     ?O     ?O     ?O  2   P     BP     RP     oP     ?P     ?P     ?P     ?P  +   ?P     Q     1Q     GQ     ^Q     pQ     ?Q     ?Q     ?Q  *   ?Q     ?Q  	   ?Q      R  !   R  
   4R  
   ?R  
   JR  [   UR     ?R  	   ?R     ?R  "   ?R     ?R      S     S     S  	   #S     -S  #   @S     dS     uS     ?S     ?S     ?S     ?S     ?S  
   ?S  	   T     T     T     3T     BT  H   PT     ?T     ?T  ,   ?T     ?T     	U     U     $U     =U     WU  !   oU     ?U     ?U     ?U     ?U     ?U     ?U     ?U  4   ?U     ?U     V     3V     MV     cV     {V     ?V     ?V  (   ?V  	   ?V  "   ?V     W  3   W     CW     SW  	   ZW     dW     ?W     ?W     ?W     ?W     ?W     ?W  !   ?W     ?W  !   X     *X     HX     ZX  	   aX     kX     ?X      ?X     ?X  +   ?X  /   ?X  ,   #Y     PY     nY     ?Y     ?Y     ?Y     ?Y     ?Y     ?Y     ?Y     ?Y  
   Z     Z     0Z     8Z     VZ     uZ     |Z     ?Z     ?Z  
   ?Z     ?Z     ?Z     ?Z  %   ?Z  	   [  #   [     5[     E[     J[  $   V[     {[     ?[     ?[         ]   ?   )   <   m   S   d           :   |   w       [      i   '   ?   3             ?       .   ?   ?           0           ^   ?           Z   r       F   =   T   {   p           ?   u   W       Y           ?       v      ?       Q   N       O   R      8              ?   k   ?   g   _   b   n             +           "   >      1   ?       ?         $   ?   e   	   j   ?   I             c   y   \           ?   9      E   K   G   U   J   ?                      a      ?   f   4      ?   /   ?       l   ?      X   P   M   ?   o   !           ;   %       D   H      L   ?   -              5   ,   ?   h   @          2   ?   ?                              #   x       s   (   ~   A       ?   V      ?       &   t       ?          `   q   ?      }       B       7   6   C   *      z      
             ?    
            
            <p>Dear ${object.create_uid.partner_id.name},
            </p>
			<p>
				Your Activity # ${object.activity_type_id.name} 
				% if object.summary 
				"${object.summary}"
				% endif
				scheduled on ${object.date_deadline} is due.
			</p>
			
			<p>	
				% if object.note
				Note :
				${object.text_note}  
				% endif
            </p>
            <p>Thank you</p>
			 <div style="display: inline-block; margin: 15px; text-align: left">
                    <a href="/mail/view?model=${object.res_model}&amp;res_id=${object.res_id}" target="_blank"
                        style="padding: 5px 10px; color: #FFFFFF; text-decoration: none; background-color: #875A7B; border: 1px solid #875A7B; border-radius: 3px"
                    >View</a>
                </div>
															
			 
            
            <p>Dear ${object.user_id.partner_id.name},
            </p>
			<p>
				Your Activity # ${object.activity_type_id.name} 
				% if object.summary 
				"${object.summary}"
				% endif
				scheduled on ${object.date_deadline} is due.
			</p>
			
			<p>	
				% if object.note
				Note :
				${object.text_note}  
				% endif
            </p>

			<p>Thank you</p>
			 <div style="display: inline-block; margin: 15px; text-align: left">
                    <a href="/mail/view?model=${object.res_model}&amp;res_id=${object.res_id}" target="_blank"
                        style="padding: 5px 10px; color: #FFFFFF; text-decoration: none; background-color: #875A7B; border: 1px solid #875A7B; border-radius: 3px"
                    >View</a>
                </div>												
			 ${object.company_id.name} Activity Reminder(Ref ${object.res_name or 'n/a' }) ${object.create_uid.partner_id.name} # ${object.activity_type_id.name} - Activity Due Notification ${object.user_id.partner_id.name} # ${object.activity_type_id.name} - Activity Due Notification <div style="margin: 0px; padding: 0px;">
				<table border="0" width="100%" cellpadding="0" bgcolor="#ededed" style="padding: 20px; background-color: #ededed; border-collapse:separate;" summary="o_mail_notification">
                    <tbody>

                      <!-- HEADER -->
                      <tr>
                        <td align="center" style="min-width: 590px;">
                          <table width="590" border="0" cellpadding="0" bgcolor="#875A7B" style="min-width: 590px; background-color: rgb(135,90,123); padding: 20px; border-collapse:separate;">
                            <tr>
                              <td valign="middle">
                                  <span style="font-size:20px; color:white; font-weight: bold;">
                                      <strong>Activity Remainder (${object.activity_type_id.name})</strong>
                                  </span>
                              </td>
                              <td valign="middle" align="right">
                                  <img src="/logo.png?company=${object.company_id.id}" style="padding: 0px; margin: 0px; height: auto; width: 80px;" alt="${object.company_id.name}"/>
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>

                      <!-- CONTENT -->
                      <tr>
                        <td align="center" style="min-width: 590px;">
                          <table width="590" border="0" cellpadding="0" bgcolor="#ffffff" style="min-width: 590px; background-color: rgb(255, 255, 255); padding: 20px; border-collapse:separate;">
                            <tbody>
                              <td valign="top" style="font-family:Arial,Helvetica,sans-serif; color: #555; font-size: 14px;">
                                <p style="margin: 0px; padding: 0px; font-size: 13px;">
                                	<strong>${object.res_model_id.name} :</strong> ${object.res_name}
                                	<br/>
							    	<br/>
							    	<strong>Due Date : </strong> ${object.date_deadline}
							    	<br/>
							    	<br/>
							    	<strong>Summary : </strong> ${object.summary}
							    	<br/>
							    	<br/>
							    	<strong>Assigned To : </strong> ${object.user_id.name}
							    	<br/>
							    	<br/>
							    	<strong>Supervisor : </strong> ${object.supervisor_id.name}
							    	<br/>
							    	<br/>
							    	% if object.sh_user_ids:
							    		<strong>Assign Multi Users :</strong>
								    	% for row in object.sh_user_ids :
								    		<span class="badge badge-info" style="padding-right:5px">
								    			${row.name}
								    		</span>
								    	%endfor
								    	<br/>
								    	<br/>
							    	% endif
							    	% if object.sh_activity_tags:
							    		<strong>Activity Tags :</strong>
								    	% for row in object.sh_activity_tags :
								    		<span class="badge badge-info" style="padding-right:5px">
								    			${row.name}
								    		</span>
								    	%endfor
								    	<br/>
								    	<br/>
							    	% endif
							    </p>
                              </td>
                            </tbody>
                          </table>
                        </td>
                      </tr>

                      <!-- FOOTER -->
                      <tr>
                        <td align="center" style="min-width: 590px;">
                          <table width="590" border="0" cellpadding="0" bgcolor="#875A7B" style="min-width: 590px; background-color: rgb(135,90,123); padding: 20px; border-collapse:separate;">
                            <tr>
                              <td valign="middle" align="left" style="color: #fff; padding-top: 10px; padding-bottom: 10px; font-size: 12px;">
                                ${object.company_id.name}<br/>
                                ${object.company_id.phone or ''}
                              </td>
                              <td valign="middle" align="right" style="color: #fff; padding-top: 10px; padding-bottom: 10px; font-size: 12px;">
                                % if object.company_id.email:
                                <a href="mailto:${object.company_id.email}" style="text-decoration:none; color: white;">${object.company_id.email}</a><br/>
                                % endif
                                % if object.company_id.website:
                                    <a href="${object.company_id.website}" style="text-decoration:none; color: white;">
                                        ${object.company_id.website}
                                    </a>
                                % endif
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>
                    </tbody>
                </table>
			</div>
             <span>&amp;laquo;</span>
												<span class="sr-only">Previous</span> <span>&amp;raquo;</span>
												<span class="sr-only">Next</span> <strong>Recommended Activities</strong> Action Action Name Active Activities Activity Activity Alarm Activity Cancel Activity Dashboard Activity Document Model Configuration Activity Done Activity Feedback Activity Manager Activity Mixin Activity Reminder Activity Reminder () Activity Reminder ? Activity Reminder Configuration Activity Supervisor Activity Tag Activity Tags Activity Type Activity User Add Action Alarm Reminder All Activities All Activities Table Limit Applies To Archived Archived Activities Assign Multi Users Assign To Assigned To Assigned to Assigned user %s has no access to the document and is not able to handle this activity. Cancel Cancelled Cancelled Activities Cancelled Activities Table Limit Close Color Color Index Companies Company Completed Activities Completed Activities Table Limit Completed Date Config Settings Configuration Configure Activity Alarm Counter Create a new Activity Alarm Create a new Tag Created by Created on Dashboard Dashboard Configuration Data Table Deadline Date Display Dashboard Counter and Data Table Configuration Display Multi Users ? Display Name Display document model wise activity ? Document Model Document Models Done Done & Launch Next Done & Schedule Next Done Button Pressed Due Activities Table Limit Due Date Edit Email Feedback Groups Hour(s) ID Individual activities for multi users ? Last Modified on Last Updated by Last Updated on Log a note... Log an Activity Mark As Done Mark as Done Mark as done Mass Activities Dynamic Action Minute(s) Missed Activity Notify Models Multi Users in Activity Configuration My Activities Name Next No Any Data Available Note Notes Notes In Char format  Origin Origin Activity Overdue Activities Page navigation example Planned Activities Planned Activities Table Limit Please Select Model. Popup Previous Records Related Action Related Document Related Document Model Reminder Before Reminder Before can't set less than 1 Hour. Reminder Before can't set less than 300 Seconds. Reminder Before can't set less than 5 Minutes. Reminder Due Date Reminder Unit Reminders Remove Action Reporting SH Mail Activity Schedule Schedule Activity Schedule Multiple Activity Schedule an Activity Second(s) Select Date Settings Sh Activity Create Action Sh Display Multi User State State Compute Status Summary Supervisor Supervisor Activities Supervisors Tag Name Tag name already exists ! Tags The model this field belongs to Today's Meetings Type Unarchive Update Old Activity Data Users View e.g. Discuss proposal Project-Id-Version: Odoo Server 13.0+e
Report-Msgid-Bugs-To: 
PO-Revision-Date: 2021-10-22 18:08-0500
Last-Translator: 
Language-Team: 
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Plural-Forms: 
Language: es_MX
X-Generator: Poedit 3.0
 
            
            <p>Estimado ${object.create_uid.partner_id.name},
            </p>
			<p>
				Su actividad # ${object.activity_type_id.name} 
				% if object.summary 
				"${object.summary}"
				% endif
				agendada el ${object.date_deadline} esta por vencer.
			</p>
			
			<p>	
				% if object.note
				Nota :
				${object.text_note}  
				% endif
            </p>
            <p>Gracias</p>
			 <div style="display: inline-block; margin: 15px; text-align: left">
                    <a href="/mail/view?model=${object.res_model}&amp;res_id=${object.res_id}" target="_blank"
                        style="padding: 5px 10px; color: #FFFFFF; text-decoration: none; background-color: #875A7B; border: 1px solid #875A7B; border-radius: 3px"
                    >View</a>
                </div>
															
			 
            
            <p>Estimado ${object.user_id.partner_id.name},
            </p>
			<p>
				Tu actividad # ${object.activity_type_id.name} 
				% if object.summary 
				"${object.summary}"
				% endif
				agendada el ${object.date_deadline} esta por vencer.
			</p>
			
			<p>	
				% if object.note
				Nota :
				${object.text_note}  
				% endif
            </p>

			<p>Gracias</p>
			 <div style="display: inline-block; margin: 15px; text-align: left">
                    <a href="/mail/view?model=${object.res_model}&amp;res_id=${object.res_id}" target="_blank"
                        style="padding: 5px 10px; color: #FFFFFF; text-decoration: none; background-color: #875A7B; border: 1px solid #875A7B; border-radius: 3px"
                    >View</a>
                </div>												
			 ${object.company_id.name} Recordatorio de Actividad(Ref ${object.res_name or 'n/a' }) ${object.user_id.partner_id.name} # ${object.activity_type_id.name} - Notificación de Vencimiento de Actividad ${object.user_id.partner_id.name} # ${object.activity_type_id.name} - Notificación de Vencimiento de Actividad <div style="margin: 0px; padding: 0px;">
				<table border="0" width="100%" cellpadding="0" bgcolor="#ededed" style="padding: 20px; background-color: #ededed; border-collapse:separate;" summary="o_mail_notification">
                    <tbody>

                      <!-- HEADER -->
                      <tr>
                        <td align="center" style="min-width: 590px;">
                          <table width="590" border="0" cellpadding="0" bgcolor="#875A7B" style="min-width: 590px; background-color: rgb(135,90,123); padding: 20px; border-collapse:separate;">
                            <tr>
                              <td valign="middle">
                                  <span style="font-size:20px; color:white; font-weight: bold;">
                                      <strong>Recordatorio de Actividad (${object.activity_type_id.name})</strong>
                                  </span>
                              </td>
                              <td valign="middle" align="right">
                                  <img src="/logo.png?company=${object.company_id.id}" style="padding: 0px; margin: 0px; height: auto; width: 80px;" alt="${object.company_id.name}"/>
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>

                      <!-- CONTENT -->
                      <tr>
                        <td align="center" style="min-width: 590px;">
                          <table width="590" border="0" cellpadding="0" bgcolor="#ffffff" style="min-width: 590px; background-color: rgb(255, 255, 255); padding: 20px; border-collapse:separate;">
                            <tbody>
                              <td valign="top" style="font-family:Arial,Helvetica,sans-serif; color: #555; font-size: 14px;">
                                <p style="margin: 0px; padding: 0px; font-size: 13px;">
                                	<strong>${object.res_model_id.name} :</strong> ${object.res_name}
                                	<br/>
							    	<br/>
							    	<strong>Fecha Límite : </strong> ${object.date_deadline}
							    	<br/>
							    	<br/>
							    	<strong>Resumen : </strong> ${object.summary}
							    	<br/>
							    	<br/>
							    	<strong>Asignada a : </strong> ${object.user_id.name}
							    	<br/>
							    	<br/>
							    	<strong>Supervisor : </strong> ${object.supervisor_id.name}
							    	<br/>
							    	<br/>
							    	% if object.sh_user_ids:
							    		<strong>Asignación de múltiples usuarios :</strong>
								    	% for row in object.sh_user_ids :
								    		<span class="badge badge-info" style="padding-right:5px">
								    			${row.name}
								    		</span>
								    	%endfor
								    	<br/>
								    	<br/>
							    	% endif
							    	% if object.sh_activity_tags:
							    		<strong>Etiquetas de Actividad :</strong>
								    	% for row in object.sh_activity_tags :
								    		<span class="badge badge-info" style="padding-right:5px">
								    			${row.name}
								    		</span>
								    	%endfor
								    	<br/>
								    	<br/>
							    	% endif
							    </p>
                              </td>
                            </tbody>
                          </table>
                        </td>
                      </tr>

                      <!-- FOOTER -->
                      <tr>
                        <td align="center" style="min-width: 590px;">
                          <table width="590" border="0" cellpadding="0" bgcolor="#875A7B" style="min-width: 590px; background-color: rgb(135,90,123); padding: 20px; border-collapse:separate;">
                            <tr>
                              <td valign="middle" align="left" style="color: #fff; padding-top: 10px; padding-bottom: 10px; font-size: 12px;">
                                ${object.company_id.name}<br/>
                                ${object.company_id.phone or ''}
                              </td>
                              <td valign="middle" align="right" style="color: #fff; padding-top: 10px; padding-bottom: 10px; font-size: 12px;">
                                % if object.company_id.email:
                                <a href="mailto:${object.company_id.email}" style="text-decoration:none; color: white;">${object.company_id.email}</a><br/>
                                % endif
                                % if object.company_id.website:
                                    <a href="${object.company_id.website}" style="text-decoration:none; color: white;">
                                        ${object.company_id.website}
                                    </a>
                                % endif
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>
                    </tbody>
                </table>
			</div>
             <span>&amp;laquo;</span>
												<span class="sr-only">Anterior</span> <span>&amp;raquo;</span>
												<span class="sr-only">Siguiente</span> <strong>Act. Recomendadas</strong Acción Nombre de Acción Activo Actividades Actividad Alamar de Actividad Cancelar Actividad Tablero de Actividades Modelo de Documento de Configuración de Actividad Actividad Hecha Retroalimentación Actividad Gestor de Actividad Mezcla de actividades Recordatorio de Actividad Recordatorio de Actividad () Recordatorio de Actividad ? Configuración de Recordatorio de Actividad Actividad del Supervisor Etiqueta de Actividad Etiquetas de Actividad Tipo de Actividad Actividad de Usuario Añadir Acción Alarma de Recordatorio Todas las Actividades Tabla del Límite de todas las actividades Aplica a Archivado Activ. Archivadas Asignación de múltiples usuario Asignado a Asignado a Asignado a El usuario asignado %s no tiene acceso a este documento y no puede ejecutar esta actividad. Cancelar Cancelado Activ. Canceladas Tabla Límite de Activ. Canceladas Cerrar Color Índice de Color Compañías Compañia Activ. Completadas Tabla Límite de Activ. Completadas Fecha Completada Opciones de Configuración Configuración Configurar Alarma de Actividad Contador Crear nueva Alarma de Actividad Crear nueva etiqueta Creado por Creado el Tablero Configuración de Tablero Tabla de Datos Fecha Límite Mostrar el contador del tablero y la configuración de la tabla de datos ¿Mostrar múltiples usuarios? Nombre mostrado ¿Mostrar actividad del modelo de documento? Modelo de Documento Modelos de Documento Hecho Hecho y lanzar siguiente Hecho y agendar siguiente Botón Hecho presionado Tabla Límite de Activ. Atrasadas Fecha Límite Editar Email Comentarios Grupos Hora(s) ID ¿Actividades individuales para múltiples usuarios? Última modificación el Última actualización por Última actualización en Registrar una nota... Registrar una actividad Marcar como Hecho Marcar como Hecho Marcar como Hecho Acción Dinámica de Actividades Masivas Minuto(s) Notificación de Actividad Perdida Modelos Configuración de Actividad con Múltiples Usuarios Mis Actividades Nombre Siguiente No hay información disponible Nota Notas Notas en formato texto  Origen Origen de la Actividad Activ. Atrasadas Ejemplo de Página de Navegación Activ. Planeadas Tabla Límite de Activ. Planeadas Por favor seleccionar modelo. Ventana Emergente Previo Registros Actividad Relacionada Documento Relacionado Modelo del Documento Relacionado Recordar antes Recordatorio no puede ser menor a una hora. Recordatorio no puede ser menor a 300 segundos. Recordatorio no puede ser menor a 5 minutos. Recordatorio de Fecha Límite Unidad de Recodatorio Recordatorios Remover Acción Reporte SH Correo de Actividad Agendar Agendar Actividad Agendar Múltiples Actividades Planificar una actividad Segundo(s) Seleccionar Fecha Ajustes SH Crear acción de actividad SH Mostrar Múltiples usuarios Estado Estado Computado Estado Resumen Supervisor Activ(s).  del Supervisor Supervisores Nombre de Etiqueta ¡El nombre de la etiqueta ya existe! Etiquetas El modelo de este campo pertenece a Reunión de hoy Tipo Desarchivar Actualizar dato de actividad antigua Usuarios Ver ejem. Discutir Presupuesto 