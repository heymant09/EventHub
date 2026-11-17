import { useCallback, useEffect, useState } from 'react'
import { AuthContext } from '../context/AuthContext'
import { useContext } from 'react'
import { getUsers, updateUserRole } from '../api/auth'
import { createCategory, deleteCategory, getCategories, updateCategory } from '../api/events'
import './AdminWorkspace.css'

const PAGE_SIZE = 50
const roles = ['attendee', 'organiser', 'admin']

function errorText(error) {
  const detail = error.response?.data?.detail
  return Array.isArray(detail) ? detail.map((item) => item.msg).join(' ') : detail || 'Please try again.'
}

export default function AdminWorkspace() {
  const { user: currentUser } = useContext(AuthContext)
  const [users, setUsers] = useState([])
  const [categories, setCategories] = useState([])
  const [roleDrafts, setRoleDrafts] = useState({})
  const [categoryDraft, setCategoryDraft] = useState({ name: '', description: '' })
  const [editingCategory, setEditingCategory] = useState(null)
  const [skip, setSkip] = useState(0)
  const [hasMoreUsers, setHasMoreUsers] = useState(false)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const loadData = useCallback(async (offset = skip) => {
    try {
      const [userData, categoryData] = await Promise.all([
        getUsers({ skip: offset, limit: PAGE_SIZE }),
        getCategories(),
      ])
      setUsers(userData)
      setRoleDrafts(Object.fromEntries(userData.map((item) => [item.id, item.role])))
      setCategories(categoryData)
      setHasMoreUsers(userData.length === PAGE_SIZE)
    } catch (err) {
      setError(errorText(err))
    } finally {
      setLoading(false)
    }
  }, [skip])

  useEffect(() => { loadData(skip) }, [loadData, skip])

  async function submitCategory(event) {
    event.preventDefault()
    setBusy('category')
    setError('')
    try {
      const created = await createCategory({ name: categoryDraft.name.trim(), description: categoryDraft.description.trim() || null })
      setCategories((current) => [...current, created].sort((a, b) => a.name.localeCompare(b.name)))
      setCategoryDraft({ name: '', description: '' })
      setNotice('Category created.')
    } catch (err) { setError(errorText(err)) }
    finally { setBusy('') }
  }

  async function saveCategory(event) {
    event.preventDefault()
    setBusy(`category-${editingCategory.id}`)
    setError('')
    try {
      const updated = await updateCategory(editingCategory.id, { name: editingCategory.name.trim(), description: editingCategory.description.trim() || null })
      setCategories((current) => current.map((item) => item.id === updated.id ? updated : item).sort((a, b) => a.name.localeCompare(b.name)))
      setEditingCategory(null)
      setNotice('Category updated.')
    } catch (err) { setError(errorText(err)) }
    finally { setBusy('') }
  }

  async function removeCategory(category) {
    if (!window.confirm(`Delete “${category.name}”? It will also be removed from events that use it.`)) return
    setBusy(`category-${category.id}`)
    setError('')
    try {
      await deleteCategory(category.id)
      setCategories((current) => current.filter((item) => item.id !== category.id))
      setNotice('Category deleted.')
    } catch (err) { setError(errorText(err)) }
    finally { setBusy('') }
  }

  async function saveRole(user) {
    const role = roleDrafts[user.id]
    if (role === user.role) return
    if (user.id === currentUser?.id && role !== 'admin') {
      setError('You cannot remove your own admin access here. Ask another administrator to change your role.')
      setRoleDrafts((current) => ({ ...current, [user.id]: user.role }))
      return
    }
    setBusy(`user-${user.id}`)
    setError('')
    try {
      const updated = await updateUserRole(user.id, role)
      setUsers((current) => current.map((item) => item.id === updated.id ? updated : item))
      setRoleDrafts((current) => ({ ...current, [updated.id]: updated.role }))
      setNotice(`Role updated for ${updated.name}.`)
    } catch (err) {
      setError(errorText(err))
      setRoleDrafts((current) => ({ ...current, [user.id]: user.role }))
    } finally { setBusy('') }
  }

  function changePage(nextSkip) {
    setLoading(true)
    setError('')
    setSkip(nextSkip)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return <main className="content admin-workspace">
    <div className="eyebrow muted">EVENTHUB CONTROL ROOM</div>
    <header className="admin-heading"><div><h1>Admin <em>workspace.</em></h1><p>Manage community categories and account roles.</p></div><button className="admin-secondary" onClick={() => { setLoading(true); setError(''); loadData(skip) }} disabled={loading}>Refresh data</button></header>
    {notice && <div className="admin-notice" role="status">{notice}<button onClick={() => setNotice('')} aria-label="Dismiss">×</button></div>}
    {error && <div className="admin-error" role="alert">{error}<button onClick={() => { setLoading(true); setError(''); loadData(skip) }}>Retry</button></div>}

    <section className="admin-section"><div className="admin-section-heading"><div><div className="eyebrow muted">DISCOVERY</div><h2>Event categories <span>{categories.length}</span></h2></div></div>
      <form className="admin-category-create" onSubmit={submitCategory}><label>Category name<input required minLength="2" maxLength="100" value={categoryDraft.name} onChange={(event) => setCategoryDraft({ ...categoryDraft, name: event.target.value })} placeholder="e.g. Live music"/></label><label>Description <small>optional</small><input value={categoryDraft.description} onChange={(event) => setCategoryDraft({ ...categoryDraft, description: event.target.value })} placeholder="What belongs in this category?"/></label><button className="admin-primary" disabled={busy === 'category'}>{busy === 'category' ? 'Adding…' : 'Add category'}</button></form>
      {loading && !categories.length ? <div className="admin-state">Loading categories…</div> : categories.length ? <div className="admin-category-list">{categories.map((category) => <article className="admin-category-row" key={category.id}>{editingCategory?.id === category.id ? <form className="admin-category-edit" onSubmit={saveCategory}><input aria-label="Category name" required minLength="2" maxLength="100" value={editingCategory.name} onChange={(event) => setEditingCategory({ ...editingCategory, name: event.target.value })}/><input aria-label="Category description" value={editingCategory.description || ''} onChange={(event) => setEditingCategory({ ...editingCategory, description: event.target.value })}/><button className="admin-primary" disabled={busy === `category-${category.id}`}>Save</button><button type="button" className="admin-secondary" onClick={() => setEditingCategory(null)}>Discard</button></form> : <><div><strong>{category.name}</strong><small>{category.description || 'No description'}</small></div><div className="admin-row-actions"><button className="admin-secondary" onClick={() => setEditingCategory({ ...category })}>Edit</button><button className="admin-danger" onClick={() => removeCategory(category)} disabled={busy === `category-${category.id}`}>{busy === `category-${category.id}` ? 'Deleting…' : 'Delete'}</button></div></>}</article>)}</div> : <div className="admin-state">No categories have been added yet.</div>}
    </section>

    <section className="admin-section"><div className="admin-section-heading"><div><div className="eyebrow muted">ACCESS CONTROL</div><h2>Users <span>{users.length}{hasMoreUsers ? '+' : ''}</span></h2></div><div className="admin-pagination"><button className="admin-secondary" disabled={skip === 0 || loading} onClick={() => changePage(Math.max(0, skip - PAGE_SIZE))}>Previous</button><span>Page {Math.floor(skip / PAGE_SIZE) + 1}</span><button className="admin-secondary" disabled={!hasMoreUsers || loading} onClick={() => changePage(skip + PAGE_SIZE)}>Next</button></div></div>
      {loading ? <div className="admin-state">Loading users…</div> : users.length ? <div className="admin-user-list">{users.map((account) => <article className="admin-user-row" key={account.id}><div className="admin-user-avatar" aria-hidden="true">{account.name.slice(0, 1).toUpperCase()}</div><div className="admin-user-identity"><strong>{account.name}{account.id === currentUser?.id && <small>you</small>}</strong><span>{account.email}</span></div><span className={`admin-account-state ${account.is_active ? 'is-active' : 'is-inactive'}`}>{account.is_active ? 'Active' : 'Inactive'}</span><select aria-label={`Role for ${account.name}`} value={roleDrafts[account.id] || account.role} onChange={(event) => setRoleDrafts((current) => ({ ...current, [account.id]: event.target.value }))}>{roles.map((role) => <option key={role} value={role}>{role}</option>)}</select><button className="admin-secondary" onClick={() => saveRole(account)} disabled={busy === `user-${account.id}` || (roleDrafts[account.id] || account.role) === account.role}>{busy === `user-${account.id}` ? 'Saving…' : 'Save role'}</button></article>)}</div> : <div className="admin-state">No users found.</div>}
    </section>
    <footer className="page-footer"><span>GOOD PLANS. GOOD PEOPLE.</span><span>MADE FOR SHOWING UP <b>✦</b></span></footer>
  </main>
}
