{{- define "safework.name" -}}
{{- default .Chart.Name .Values.nameOverride  < /dev/null |  trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "safework.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{- define "safework.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "safework.labels" -}}
helm.sh/chart: {{ include "safework.chart" . }}
{{ include "safework.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "safework.selectorLabels" -}}
app.kubernetes.io/name: {{ include "safework.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
