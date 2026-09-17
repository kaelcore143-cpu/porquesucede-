---
layout: article.njk
title: ¿Cómo funciona el correo electrónico?
description: Descubre cómo viaja un correo electrónico desde que pulsas enviar hasta que llega al destinatario.
category: Tecnología
tags: [tecnologia]
keywords: []
read_time: 5 min
short_answer: Un correo electrónico viaja desde tu cliente de correo a tu servidor SMTP, que lo enruta por Internet a través de servidores intermedios hasta el servidor del destinatario, donde queda almacenado hasta que lo descarga.
permalink: /tecnologia/cómo-funciona-el-correo-electrónico/
breadcrumbs:
  - name: Tecnología
    url: /tecnologia/
  - name: ¿Cómo funciona el correo electrónico?
    url: /tecnologia/cómo-funciona-el-correo-electrónico
structured_data: '{"@context": "https://schema.org", "@graph": [{"@type": "Article", "headline": "¿Cómo funciona el correo electrónico?", "description": "Descubre cómo viaja un correo electrónico desde que pulsas enviar hasta que llega al destinatario.", "mainEntityOfPage": "https://porquesucede.com/tecnologia/cómo-funciona-el-correo-electrónico/", "url": "https://porquesucede.com/tecnologia/cómo-funciona-el-correo-electrónico/", "inLanguage": "es", "publisher": {"@type": "Organization", "name": "PorQuéSucede"}}, {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Inicio", "item": "https://porquesucede.com/"}, {"@type": "ListItem", "position": 2, "name": "Tecnología", "item": "https://porquesucede.com/tecnologia/"}, {"@type": "ListItem", "position": 3, "name": "¿Cómo funciona el correo electrónico?"}]}]}'
related_articles:
  - title: ¿Cómo funciona Internet?
    url: /tecnologia/como-funciona-internet/
  - title: ¿Qué es la ciberseguridad?
    url: /tecnologia/que-es-la-ciberseguridad/
  - title: ¿Cómo funciona el WiFi?
    url: /tecnologia/como-funciona-el-wifi/
---

## Los protocolos del correo

El correo usa tres protocolos principales: **SMTP** (Simple Mail Transfer Protocol) para enviar, **IMAP** o **POP3** para recibir y descargar. SMTP es el cartero; IMAP te permite ver el correo en el servidor sin descargarlo; POP3 lo descarga y elimina del servidor.

## El viaje del mensaje

Al pulsar 'enviar': tu cliente de correo lo envía a tu servidor SMTP. Ese servidor consulta el DNS para encontrar el servidor del dominio del destinatario (el registro MX). Establece conexión SMTP con ese servidor y transfiere el mensaje. El destinatario lo descarga con IMAP/POP3.

## Spam y seguridad

Los servidores de correo emplean sistemas anti-spam que analizan el contenido, verifican la reputación del servidor remitente y comprueban registros DNS de autenticación (SPF, DKIM, DMARC). A pesar de todo, el 45% de todos los correos mundiales son spam.

## Datos curiosos

- El primer correo electrónico se envió en 1971 por Ray Tomlinson, que eligió la @ para separar usuario de máquina.
- Se envían unos 330.000 millones de correos electrónicos al día en el mundo.
- El correo electrónico es más eficiente energéticamente que el correo postal para el mismo volumen de comunicación.

## Conclusión

El correo electrónico es uno de los sistemas de comunicación más resistentes de la historia digital. Con más de 50 años de uso ininterrumpido, sus protocolos básicos siguen vigentes, adaptados a un mundo de miles de millones de usuarios.