Feature: Advanced testing of Product, ShoppingCart and Order

  Scenario: Product is available in exact amount
    Given a product with name "Phone", price 1000 and availability 5
    When I check product availability for amount 5
    Then availability result should be True

  Scenario: Product is not available in greater amount
    Given a product with name "Phone", price 1000 and availability 5
    When I check product availability for amount 6
    Then availability result should be False

  Scenario: Product is available for zero amount
    Given a product with name "Phone", price 1000 and availability 5
    When I check product availability for amount 0
    Then availability result should be True

  Scenario: Buying product decreases available amount
    Given a product with name "Phone", price 1000 and availability 5
    When I buy product in amount 2
    Then product availability should become 3

  Scenario: Adding available product to shopping cart
    Given a product with name "Phone", price 1000 and availability 5
    And an empty shopping cart
    When I add the product to cart in amount 2
    Then product should be in the cart

  Scenario: Adding unavailable product to shopping cart
    Given a product with name "Phone", price 1000 and availability 5
    And an empty shopping cart
    When I add the product to cart in amount 10
    Then add to cart operation should fail

  Scenario: Shopping cart total is calculated correctly
    Given a product with name "Phone", price 1000 and availability 5
    And an empty shopping cart
    When I add the product to cart in amount 3
    Then cart total should be 3000

  Scenario: Removing product from shopping cart
    Given a product with name "Phone", price 1000 and availability 5
    And an empty shopping cart
    When I add the product to cart in amount 2
    And I remove the product from the cart
    Then product should not be in the cart

  Scenario: Placing order clears shopping cart
    Given a product with name "Phone", price 1000 and availability 5
    And an empty shopping cart
    When I add the product to cart in amount 2
    And I create an order from the cart
    And I place the order
    Then shopping cart should become empty

  Scenario: Adding None as product to shopping cart
    Given an empty shopping cart
    When I try to add None product to cart
    Then add to cart operation should fail
