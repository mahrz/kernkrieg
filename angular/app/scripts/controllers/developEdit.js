angular.module('kkApp')
.controller('DevelopEditCtrl',
  ['$scope', '$http', '$location', 'warrior', 'Warrior',
  function ($scope, $http, $location, warrior, Warrior)
  {
    $scope.warrior = warrior;

    $scope.saveWarrior = function ()
    {
      $scope.warrior.$update();
    }

  }]);