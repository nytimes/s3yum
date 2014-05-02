# semi-transparent http 1.1 webproxy for AWS instances with roles
# Version: 1.4.1b

http = require 'http'
url = require 'url'
qs = require 'querystring'

{createHmac} = require 'crypto'

argv = require('optimist')
  .usage("" +
    "http1.1 webproxy for a role-initiated instance." +
    "\nTransparent EXCEPT will sign GET requests for which match parameter input matches the URI." +
    "\nUsage: $0")
  .demand('host_match').describe('host_match', 'request.headers.host regexp').default('host_match', 'amazonaws\\.com')
  .boolean('debug')
  .argv

# Daemonize:
require('daemon')();

# Pid file:
npid = require('npid')
npid.create('/var/run/yum_proxyd.pid')

host_match_regexp = new RegExp(argv.host_match, 'i')
console.log "http1.1 signing webproxy - signs GET requests for AWS resources using the instance role credentials"

role = "" # role is retrieved from instance metadata and is an immutable attribute of the instance
get_role = (callback) ->
  options = hostname:"169.254.169.254", path:"/latest/meta-data/iam/security-credentials/"

  role_request = http.get options, (role_response) ->
    role_response.on 'data', (chunk) -> role += chunk # get each chunk

    role_response.on 'end', -> # on end we have the role
      console.log "\nretrieved role: #{role}"
      callback()

  role_request.on 'error', (e) -> 
    console.log "problem with role_request: #{e.message}"
    process.exit 1

credentials = {} # credentials are retrieved by role from instance metadata
renew_credentials = (callback = null) ->
  options = hostname:"169.254.169.254", path:"/latest/meta-data/iam/security-credentials/#{role}"
  data = ""

  credentials_request = http.get options, (credentials_response) ->
    credentials_response.on 'data', (chunk) -> data += chunk # get each chunk

    credentials_response.on 'end', -> # on end parse out the credentials
      console.log "\nrenewed security-credentials: #{data}" if argv.debug
      {SecretAccessKey, AccessKeyId, Token, Expiration} = JSON.parse data
      credentials = SecretAccessKey:SecretAccessKey, AccessKeyId:AccessKeyId, Token:Token
      # re-renew 4 min prior to expiration - credentials are guaranteed to be good for at least 5 min
      setTimeout renew_credentials, ((new Date(Expiration)).getTime() - (4 * 60 * 1000)) - (new Date().getTime())
      callback?() # if there is a callback then call it

  credentials_request.on 'error', (e) -> 
    console.log "problem with credentials_request: #{e.message}"
    process.exit 2

build_querystring_signature = (host, pathname, url_query, expire_seconds = 60) ->
  expires = Math.floor((new Date().getTime())/1000) + expire_seconds
  sign_pathname = "/" + host.replace(".s3.amazonaws.com","") + pathname
  string_to_sign = "GET\n\n\n#{expires}\n"
  string_to_sign += "x-amz-security-token:#{credentials.Token}\n"
  string_to_sign += encodeURI sign_pathname
  string_to_sign += "?#{url_query}" if url_query?
  signature = createHmac('sha1', credentials.SecretAccessKey).update(string_to_sign).digest('base64')
  query = Expires:expires, AWSAccessKeyId:credentials.AccessKeyId, Signature:encodeURI(signature)
  query["x-amz-security-token"] = credentials.Token
  querystring = qs.stringify query
  querystring += "&#{url_query}" if url_query?
  querystring

proxy_server = http.createServer (request, response) ->
  {host} = request.headers
  {pathname, path, query} = url.parse(request.url)

  # only sign GET requests for AWS resources, otherwise just transparently proxy the request
  if request.method is 'GET' and host.match(host_match_regexp)
    querystring = build_querystring_signature host, pathname, query # 'acl' and 'torrent' are valid query values for s3
    path = "#{pathname}?#{querystring}"

  console.log "\nmethod:#{request.method}; host: #{host}; path:#{path}" if argv.debug
  options = method:request.method, hostname:host, path:path

  do (response) ->
    remote_request = http.request options, (remote_response) ->
      response.writeHead remote_response.statusCode, remote_response.headers
      remote_response.on 'data', (chunk) -> response.write chunk, 'binary'
      remote_response.on 'end', -> response.end()

    remote_request.on 'error', (e) -> console.log "problem with remote_request: #{e.message}; method:#{request.method}; host: #{host}; path:#{path}"
    request.addListener 'data', (chunk) -> remote_request.write chunk, 'binary'
    request.addListener 'end', -> remote_request.end()

# cascade: get the instance IAM role, then initialize credentials, then start the proxy server

get_role -> renew_credentials -> proxy_server.listen 8080
