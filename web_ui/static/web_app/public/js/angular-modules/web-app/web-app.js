/* Global variables */
TOKEN_TIMEOUT = "Token was invalid (Error: Token timeout)";

var appModule = angular.module('appModule',['ngRoute','ngAnimate'])

/*  Filters    */

// Tells if an object is instance of an array type. Used primary within ng-templates
appModule.filter('isArray', function() {
  return function (input) {
    return angular.isArray(input);
  };
});


// Add new item to list checking first if it has not being loaded and if it is not null.
// Used primary within ng-templates
appModule.filter('append', function() {
  return function (input, item) {
    if (item){
        for (i = 0; i < input.length; i++) {
            if(input[i] === item){
                return input;
            }
        }
        input.push(item);
    }
    return input;
  };
});

// Remove item from list. Used primary within ng-templates
appModule.filter('remove', function() {
  return function (input, item) {
    input.splice(input.indexOf(item),1);
    return input;
  };
});

// Capitalize the first letter of a word
appModule.filter('capitalize', function() {

  return function(token) {
      return token.charAt(0).toUpperCase() + token.slice(1);
   }
});

// Replace any especial character for a space
appModule.filter('removeSpecialCharacters', function() {

  return function(token) {
      return token.replace(/#|_|-|$|!|\*/g,' ').trim();
   }
});

/*  Configuration    */

// Application routing
appModule.config(function($routeProvider, $locationProvider){
    // Maps the URLs to the templates located in the server
    $routeProvider
        .when('/', {templateUrl: 'ng/home'})
        .when('/home', {templateUrl: 'ng/home'})
        .when('/login', {templateUrl: 'ng/login'})
    $locationProvider.html5Mode(true);
});

// Add to all requests the authorization header
appModule.config(function ($httpProvider){

    $httpProvider.interceptors.push('authInterceptor');
});


appModule.filter('capitalize', function() {
    // Capitalize the first letter of a word
  return function(token) {
      return token.charAt(0).toUpperCase() + token.slice(1);
   }
});

// To avoid conflicts with other template tools such as Jinja2, all between {a a} will be managed by ansible instead of {{ }}
appModule.config(['$interpolateProvider', function($interpolateProvider) {
  $interpolateProvider.startSymbol('{a');
  $interpolateProvider.endSymbol('a}');
}]);

/* Factories */

// The notify factory allows services to notify to an specific controller when they finish operations
appModule.factory('NotifyingService' ,function($rootScope) {
    return {
        subscribe: function(scope, event_name, callback) {
            var handler = $rootScope.$on(event_name, callback);
            scope.$on('$destroy', handler);
        },

        notify: function(event_name) {
            $rootScope.$emit(event_name);
        }
    };
});

// The auth notify factory allows other components subscribe and being notified when authentication is successful
appModule.factory('AuthNotifyingService', function($rootScope) {
    return {
        subscribe: function(scope, callback) {
            var handler = $rootScope.$on('notifying-auth-event', callback);
            scope.$on('$destroy', handler);
        },

        notify: function() {
            $rootScope.$emit('notifying-auth-event');
        }
    };
});

// This factory adds the token to each API request
appModule.factory("authInterceptor", function($rootScope, $q, $window){
    return {
        request: function(config){
            config.headers = config.headers  || {};
            if ($window.sessionStorage.token){
                config.headers.Authorization = 'APIC-TOKEN ' + $window.sessionStorage.token;
            }
            return config;
        },
        responseError: function(rejection){
            if (rejection.status === 401){
                //Manage common 401 actions
            }
            return $q.reject(rejection);
        }
    };
});

/*  Services    */

/* Authentication */
appModule.service("AuthService", function($window, $http, $location, AuthNotifyingService){
    function url_base64_decode(str){
        return window.atob(str)
    }

    this.url_base64_decode = url_base64_decode

    // if token is not stored, try to get it if not in login page
    if ($location.$$path != '/login'){
        if (!$window.sessionStorage.token){
            $http
            .get('api/token')
            .then(function (response, status, headers, config){
                $window.sessionStorage.token = response.data.token;
                AuthNotifyingService.notify();
            })
            .catch(function(response, status, headers, config){
                // Any issue go to login
                $window.location.href = '/login'
            })

        }
    }
})


/*  Controllers    */

appModule.controller('AuthController', function($scope, $http, $window, AuthService, AuthNotifyingService){

    $scope.user = {username: '', password: ''}
    $scope.isAuthenticated = false
    $scope.token = $window.sessionStorage.token;

    $scope.submit = function (){
        $scope.message = "Working...";
        $http
            .post('/api/login/token', $scope.user)
            .then(function (response, status, headers, config){
                $window.sessionStorage.token = response.data.token;
                $scope.token = $window.sessionStorage.token;
                $scope.isAthenticated = true;
                $scope.message = "Success! Loading application";
                $window.location.href = '/web/'
            })
            .catch(function(response, status, headers, config){
                delete $window.sessionStorage.token;
                $scope.isAuthenticated = false;
                $scope.message = response.data;
            })
    }

    $scope.logout = function() {
        $scope.isAuthenticated = false;
        $window.sessionStorage.token = '';
        $window.location.href = '/web/logout'
    }

    AuthNotifyingService.subscribe($scope, function updateToken() {
        $scope.token = $window.sessionStorage.token;
    });
});


// App controller is in charge of managing all services for the application
appModule.controller('AppController', function($scope, $location, $http, $window, $rootScope){

    $scope.apic = {logged:false};
    $scope.loading = false;

    // Functions
    $scope.init = function(){
        // Variables

        $scope.pods = [];
        $scope.selected_pod = {};
        $scope.switches = [];
        $scope.epgs = [];
        $scope.selected_switch = {};
        $scope.error = "";
        $scope.deployment = {}
        $scope.deployment.interfaces1 = []
        $scope.deployment.interfaces2 = []
    }

    $scope.init();

    $scope.go = function ( path ) {
        $location.path( path );
    };

    $scope.setAction = function(action){
        $scope.deployment.action = action;
    }
     $scope.setVMType = function(vmType){
        $scope.deployment.vmType = vmType;
    }

    $scope.setPortType = function(portType){
        $scope.deployment.portType = portType;
    }


    $scope.setEpgAction = function(epgAction){
        $scope.deployment.epgAction = epgAction;
    }


    $scope.login = function(){
        $http
            .post('api/login/get_token', {'apic': $scope.apic })
            .then(function (response, status, headers, config){
                $window.sessionStorage.token = response.data.apic.token + " " + response.data.apic.url;
                $scope.apic.logged = true;
                $scope.getPods();
                $scope.getEpgs();
                $scope.go("/");
            })
            .catch(function(response, status, headers, config){
                $scope.error = response.data.message
            })
            .finally(function(){
            })
    };

    $scope.logout = function(){
        $scope.apic = {logged:false};
    }


    $scope.getPods = function(){

        $scope.deployment.interfaces = []
        $scope.deployment.selectedSwitch1 = {}
        $scope.deployment.selectedSwitch2 = {}
        $scope.deployment.switches = []
        $scope.deployment.selectedSwitch1 = {}
        $scope.deployment.selectedSwitch2 = {}
        $scope.pods = [];

        $http
            .get('api/pod')
            .then(function (response, status, headers, config){
                $scope.pods = response.data
            })
            .catch(function(response, status, headers, config){
                $scope.error = response.data.message
            })
            .finally(function(){
            })
    };

    $scope.getSwitches = function(pod){
        if(pod.fabricPod){
            $http
                .post('api/switch/get', {'pod': pod })
                .then(function (response, status, headers, config){
                    $scope.switches = response.data
                })
                .catch(function(response, status, headers, config){
                    $scope.error = response.data.message
                })
                .finally(function(){
                })
        }
    };

    $scope.getInterfaces1 = function(selected_switch){
        if(selected_switch.fabricNode){
            $http
                .post('api/interface/get', {'switch': selected_switch })
                .then(function (response, status, headers, config){
                    $scope.interfaces1 = response.data
                })
                .catch(function(response, status, headers, config){
                    $scope.error = response.data.message
                })
                .finally(function(){
                })
        }
    };

    $scope.getInterfaces2 = function(selected_switch){
        if(selected_switch.fabricNode){
            $http
                .post('api/interface/get', {'switch': selected_switch })
                .then(function (response, status, headers, config){
                    $scope.interfaces2 = response.data
                })
                .catch(function(response, status, headers, config){
                    $scope.error = response.data.message
                })
                .finally(function(){
                })
        }
    };

    $scope.getEpgs = function(){

        $http
            .get('api/epgs')
            .then(function (response, status, headers, config){
                $scope.epgs = response.data
            })
            .catch(function(response, status, headers, config){
                $scope.error = response.data.message
            })
            .finally(function(){
            })

    };


    $scope.deploy = function(){
        $scope.loading = true;
        $http
            .post('api/deploy', {'deployment': $scope.deployment })
            .then(function (response, status, headers, config){

            })
            .catch(function(response, status, headers, config){
                $scope.error = response.data.message
            })
            .finally(function(){
                $scope.loading = false;
            })

    };


    $scope.clearError = function(){
        $scope.error = "";
    };


    // Location logic. This tells the controller what to do according the URL that the user currently is
    $scope.$on('$viewContentLoaded', function(event) {
        if ($location.$$path === '/'){

        }
    });

    $rootScope.$on("$routeChangeStart", function(){
        if (!$scope.apic.logged){
            $scope.go('/login');
        }
        if ($location.$$path === '/logout'){
            $window.sessionStorage.token = "";
            $scope.apic = {logged:false};
            $('#menu_toggle').click();
            $scope.go('/login');
        }
         if ($location.$$path === '/'){
            $scope.init();

        }
    })
});
