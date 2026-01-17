import pytest
from httpx import AsyncClient
from src import security

pytestmark = pytest.mark.usefixtures("db")

async def create_post(body: str, async_client: AsyncClient, logged_in_token: str) -> dict:
    response = await async_client.post(
        "/api/posts", 
        json={"body": body}, 
        headers={"Authorization": f"Bearer {logged_in_token}"}
    )
    return response.json()

async def like_post(
    post_id: int, 
    async_client: AsyncClient, 
    logged_in_token: str
) -> dict:
    
    response = await async_client.post(
        "/api/like",
        json={"post_id": post_id},
        headers={"Authorization": f"Bearer {logged_in_token}"}
    )
    
    return response.json()

async def create_comment(
        body: str, 
        post_id: int, 
        async_client: AsyncClient, 
        logged_in_token: str
    ) -> dict:

    response = await async_client.post(
        "/api/posts/comment",
        json={"body": body, "post_id": post_id},
        headers={"Authorization": f"Bearer {logged_in_token}"}
    )
    return response.json()

@pytest.fixture()
async def created_post(async_client: AsyncClient, logged_in_token: str):
    return await create_post("Test post", async_client, logged_in_token)

@pytest.fixture()
async def created_comment(
    async_client: AsyncClient, 
    created_post: dict, 
    logged_in_token: str
):
    return await create_comment(
        "Test comment", 
        created_post["id"], 
        async_client, 
        logged_in_token
    )

@pytest.mark.anyio
async def test_create_post(
    async_client: AsyncClient, 
    confirmed_user: dict, 
    logged_in_token: str
):
    body = "Test post"

    response = await async_client.post(
        "/api/posts", 
        json={"body": body}, 
        headers={"Authorization": f"Bearer {logged_in_token}"}
    )

    assert response.status_code == 201
    assert {
        "id": 1, 
        "body": body, 
        "user_id": confirmed_user["id"],
        "image_url": None
    }.items() <= response.json().items()

@pytest.mark.anyio
async def test_create_post_expired_token(
    async_client: AsyncClient,
    confirmed_user: dict,
    mocker
):
    mocker.patch("src.security.access_token_expire_minutes", return_value = -1)
    token = security.create_access_token(confirmed_user["email"])

    response = await async_client.post(
        "/api/posts",
        json={"body": "Test post!"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401
    assert "Token has expired" in response.json()["detail"]

@pytest.mark.anyio
async def test_create_post_with_missing_data(async_client: AsyncClient, logged_in_token: str):
    response = await async_client.post(
        "/api/posts", 
        json={},
        headers={"Authorization": f"Bearer {logged_in_token}"}
    )

    assert response.status_code == 422

@pytest.mark.anyio
async def test_get_all_posts(async_client: AsyncClient, created_post: dict):
    response = await async_client.get("/api/posts")

    assert response.status_code == 200
    assert created_post.items() <= response.json()[0].items()

@pytest.mark.anyio
async def test_get_all_posts_sorting(
    async_client: AsyncClient, 
    logged_in_token: str
):
    await create_post("Test Post 1", async_client, logged_in_token)
    await create_post("Test Post 2", async_client, logged_in_token)

    response = await async_client.get("/api/posts", params={"sorting": "new"})
    assert response.status_code == 200

    data = response.json()
    expected_order = [2, 1]
    post_ids = [post["id"] for post in data]
    assert post_ids == expected_order

@pytest.mark.anyio
async def test_get_all_posts_sorting_from_old(
    async_client: AsyncClient, 
    logged_in_token: str
):
    await create_post("Test Post 1", async_client, logged_in_token)
    await create_post("Test Post 2", async_client, logged_in_token)

    response = await async_client.get("/api/posts", params={"sorting": "old"})
    assert response.status_code == 200

    data = response.json()
    expected_order = [1, 2]
    post_ids = [post["id"] for post in data]
    assert post_ids == expected_order

@pytest.mark.anyio
async def test_get_all_posts_sort_likes(
    async_client: AsyncClient, 
    logged_in_token: str
):
    await create_post("Test Post 1", async_client, logged_in_token)
    await create_post("Test Post 2", async_client, logged_in_token)

    await like_post(1, async_client, logged_in_token)

    response = await async_client.get("/api/posts", params={"sorting": "most_likes"})
    assert response.status_code == 200

    data = response.json()
    post_ids = [post["id"] for post in data]
    expected_order = [1, 2]
    assert post_ids == expected_order

@pytest.mark.anyio
async def test_create_comment(
    async_client: AsyncClient, 
    created_post: dict,
    confirmed_user: dict,
    logged_in_token: str
):
    
    body = "Test comment"

    response = await async_client.post(
        "/api/posts/comment",
        json={"body": body, "post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"}
    )

    assert response.status_code == 201
    assert {
        "id": 1,
        "body": body,
        "post_id": created_post["id"],
        "user_id": confirmed_user["id"]
    }.items() <= response.json().items()

@pytest.mark.anyio
async def test_get_comments_on_post(
    async_client: AsyncClient,
    created_post: dict, 
    created_comment: dict
):
    response = await async_client.get(f"/api/posts/{created_post['id']}/comment")

    assert response.status_code == 200
    assert response.json() == [created_comment]

@pytest.mark.anyio
async def test_get_no_comments_on_post(async_client: AsyncClient, created_post: dict):

    response = await async_client.get(f"/api/posts/{created_post['id']}/comment")

    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.anyio
async def test_get_single_post_with_its_comments(
    async_client: AsyncClient, 
    created_post: dict,
    created_comment: dict
):
    response = await async_client.get(f"/api/posts/{created_post['id']}")

    assert response.status_code == 200
    assert response.json() == {
        "post": {**created_post, "likes": 0}, 
        "comments": [created_comment]
    }

@pytest.mark.anyio
async def test_get_missing_post_with_comments(
    async_client: AsyncClient,
    created_post: dict,
    created_comment: dict
):
    response = await async_client.get("/api/posts/2")
    assert response.status_code == 404

@pytest.mark.anyio
async def test_like_post(
    async_client: AsyncClient,
    created_post: dict,
    logged_in_token: str
):
    response = await async_client.post(
        "/api/like",
        json={"post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == 201


@pytest.mark.anyio
async def test_delete_post(
    async_client: AsyncClient,
    created_post: dict,
    logged_in_token: str
):
    # Verify post exists initially
    response = await async_client.get(f"/api/posts/{created_post['id']}")
    assert response.status_code == 200

    # Delete the post
    response = await async_client.delete(
        f"/api/posts/{created_post['id']}",
        headers={"Authorization": f"Bearer {logged_in_token}"}
    )
    assert response.status_code == 204

    # Verify post is deleted
    response = await async_client.get(f"/api/posts/{created_post['id']}")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_post_unauthorized(
    async_client: AsyncClient,
    created_post: dict,
    logged_in_token: str,
    confirmed_user: dict
):
    # Create another user and log in
    new_user_data = {
        "email": "anotheruser@example.com",
        "password": "newpassword123",
        "username": "anotheruser"
    }
    await async_client.post("/api/register", json=new_user_data)

    login_response = await async_client.post(
        "/api/token",
        data={
            "username": new_user_data["email"],
            "password": new_user_data["password"]
        }
    )
    new_token = login_response.json()["access_token"]

    # Try to delete the post created by the original user
    response = await async_client.delete(
        f"/api/posts/{created_post['id']}",
        headers={"Authorization": f"Bearer {new_token}"}
    )
    assert response.status_code == 401
    assert "You can only delete your own posts" in response.json()["detail"]


@pytest.mark.anyio
async def test_delete_nonexistent_post(
    async_client: AsyncClient,
    logged_in_token: str
):
    # Try to delete a post that doesn't exist
    response = await async_client.delete(
        "/api/posts/9999",
        headers={"Authorization": f"Bearer {logged_in_token}"}
    )
    assert response.status_code == 404
    assert "Post not found" in response.json()["detail"]


@pytest.mark.anyio
async def test_delete_comment(
    async_client: AsyncClient,
    created_comment: dict,
    logged_in_token: str
):
    # Verify comment exists initially
    response = await async_client.get(f"/api/posts/{created_comment['post_id']}/comment")
    assert response.status_code == 200
    assert len(response.json()) == 1

    # Delete the comment
    response = await async_client.delete(
        f"/api/comments/{created_comment['id']}",
        headers={"Authorization": f"Bearer {logged_in_token}"}
    )
    assert response.status_code == 204

    # Verify comment is deleted
    response = await async_client.get(f"/api/posts/{created_comment['post_id']}/comment")
    assert response.status_code == 200
    assert len(response.json()) == 0


@pytest.mark.anyio
async def test_delete_comment_unauthorized(
    async_client: AsyncClient,
    created_post: dict,
    logged_in_token: str,
    confirmed_user: dict
):
    # Create another user and log in
    new_user_data = {
        "email": "anotheruser@example.com",
        "password": "newpassword123",
        "username": "anotheruser"
    }
    await async_client.post("/api/register", json=new_user_data)

    login_response = await async_client.post(
        "/api/token",
        data={
            "username": new_user_data["email"],
            "password": new_user_data["password"]
        }
    )
    new_token = login_response.json()["access_token"]

    # Create a comment with the new user
    response = await async_client.post(
        "/api/posts/comment",
        json={"body": "Another user's comment", "post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {new_token}"}
    )
    another_comment = response.json()

    # Try to delete the other user's comment with the original user's token
    response = await async_client.delete(
        f"/api/comments/{another_comment['id']}",
        headers={"Authorization": f"Bearer {logged_in_token}"}
    )
    assert response.status_code == 401
    assert "You can only delete your own comments" in response.json()["detail"]


@pytest.mark.anyio
async def test_delete_nonexistent_comment(
    async_client: AsyncClient,
    logged_in_token: str
):
    # Try to delete a comment that doesn't exist
    response = await async_client.delete(
        "/api/comments/9999",
        headers={"Authorization": f"Bearer {logged_in_token}"}
    )
    assert response.status_code == 404
    assert "Comment not found" in response.json()["detail"]
