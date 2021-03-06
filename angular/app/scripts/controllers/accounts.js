'use strict';

angular.module('kkApp')
.directive('ngBlur', function () {
    return function ($scope, elem, attrs) {
        elem.bind('blur', function () {
          if(!$scope.$$phase) {
            $scope.$apply(attrs.ngBlur);
          }
        });
    };
});

angular.module('kkApp')
.controller('AccountsCtrl',
  ['$scope', '$http', '$modal', '$q', 'accounts', 'User',
  function ($scope, $http, $modal, $q, accounts, User) {
    var passwordCell = '<div class="ngCellText" ng-class="col.colIndex()">' +
      '<span ng-cell-text>******</span></div>';

    var actionCell = '<button class="btn btn-danger" ng-click="deleteUser(row)" ng-disabled="row.entity.id==user_id"> Delete </button>';

    var checkCell = '<input type="checkbox" ng-class="\'colt\' + $index"' +
                   ' ng-checked="COL_FIELD" ng-model="COL_FIELD"  ng-disabled="row.entity.id==user_id"/>';

    var editCell = '<input type="text" ng-cell-input ng-class="\'colt\' + $index"' +
                   ' ng-input="COL_FIELD" ng-model="COL_FIELD" />';

    var passwordEditCell = '<input type="password" ng-cell-input' +
                   ' ng-class="\'colt\' + $index" ' +
                   ' ng-input="COL_FIELD" ng-model="passwordTemp[row.entity.id]"' +
                   ' ng-blur="updatePassword(row)" />';

    $http.get('/api/user_id').success(function(data, status, headers, config) {
        $scope.user_id =  data.user_id;
    });

    var modalPromise = $modal({template: 'app/views/elements/delete.html',
      persist: true, show: false, backdrop: 'static', scope: $scope});

    $scope.passwordTemp = {};
    _.each(accounts, function (a) { $scope.passwordTemp[a.id] = "" ;});
    $scope.accounts = accounts;
    $scope.gridAccounts =
    {
      data: 'accounts',
      enableCellSelection: true,
      enableRowSelection: false,
      rowHeight:50,
      plugins: [new ngGridFlexibleHeightPlugin(opts = { minHeight: 200})],
      columnDefs: [ { field: 'username',
                      displayName: 'Username',
                      enableCellEdit: true,
                      editableCellTemplate: editCell,
                    },
                    { field:'email',
                      displayName:'E-Mail',
                      enableCellEdit: true,
                      editableCellTemplate: editCell,
                    },
                    { field:'admin',
                      displayName:'Admin',
                      enableCellEdit: false,
                      cellTemplate: checkCell,
                    },
                    { field:'passwdHash',
                      displayName: 'Password',
                      cellTemplate: passwordCell,
                      editableCellTemplate: passwordEditCell,
                      enableCellEdit: true
                    },
                    { field: '',
                      displayName: 'Action',
                      cellTemplate: actionCell
                    } ]
    };

    $scope.updatePassword = function(row)
    {

      var user = new User(_.findWhere($scope.accounts, {id :row.entity.id}));
      user.passwdHash = $scope.passwordTemp[row.entity.id];
      if(user.passwdHash.length > 0)
      {
        user.$update(function(user) {
          $scope.passwordTemp[user.id] = "";
          },
        function() {
          $scope.passwordTemp[user.id] = "";
          });
      }
    }

    $scope.$watch('accounts', function(newValue, oldValue)
    {
      // Added an account or deleted one should not trigger an update
      // Performance wise this is not ideal, but works so far
      for (var i = newValue.length - 1; i >= 0; i--)
      {
        if(i<oldValue.length)
        {
          if(!angular.equals(oldValue[i],newValue[i]) &&
             oldValue[i].id == newValue[i].id)
          {
            // Update account
            var user = new User($scope.accounts[i]);
            user.$update(function(user) {}, function() {});
          }
        }
      }
    }, true);

    $scope.addNewUser = function ()
    {
      var user = new User({ username: "user" + $scope.accounts.length,
        email : "user" + $scope.accounts.length + "@nodomain.not",
        passwdHash : "password",
        admin : false});

      user.$save( function(user) {
        $scope.accounts.unshift(user);
        $scope.passwordTemp[user.id] = "";
      });
    };

    $scope.deleteUser = function (row)
    {
      $scope.delRow = row;
      $scope.delObject = "User";
      $q.when(modalPromise).then(function(modalEl) {
        modalEl.modal('show');
      });
    }

    $scope.doDelete = function ()
    {
      var user = new User($scope.delRow.entity);
      user.$delete(function ()
      {
        $scope.accounts = _.reject($scope.accounts, {id: $scope.delRow.entity.id})
      });
    }
  }]);